import unittest
import json
import sys
from types import SimpleNamespace
from unittest.mock import patch

from qwen_ui_pipeline.comfyui_node import (
    QwenImage3Edit,
    QwenImage3Render,
    QwenImage3TextToImage,
    ReferenceRegionComposite,
    _partner_render,
    _reference_data_urls,
)
from qwen_ui_pipeline.providers.router import ProviderResult


class QwenImage3RenderTests(unittest.TestCase):
    def test_legacy_node_still_uses_only_the_first_four_batch_images(self):
        test_case = self

        class FakePixels:
            def clip(self, _minimum, _maximum):
                return self

            def __mul__(self, _value):
                return self

            def round(self):
                return self

            def astype(self, _name):
                return self

        class FakeTensor:
            def detach(self):
                return self

            def cpu(self):
                return self

            def numpy(self):
                return FakePixels()

        class FakeImage:
            @staticmethod
            def fromarray(_pixels, mode):
                test_case.assertEqual(mode, "RGB")
                return FakeImage()

            def save(self, buffer, format):
                test_case.assertEqual(format, "PNG")
                buffer.write(b"fake-png")

        pil_module = SimpleNamespace(Image=FakeImage)
        with patch.dict(sys.modules, {"PIL": pil_module}):
            encoded = _reference_data_urls([FakeTensor() for _index in range(5)])

        self.assertEqual(len(encoded), 4)

    def test_node_accepts_an_edit_brief_but_never_an_api_key_widget(self):
        inputs = QwenImage3Render.INPUT_TYPES()
        exposed_names = set(inputs["required"]) | set(inputs["optional"])

        self.assertIn("edit_brief_json", exposed_names)
        self.assertIn("reference_images", exposed_names)
        self.assertNotIn("api_key", exposed_names)
        self.assertEqual(QwenImage3Render.CATEGORY, "Qwen UI Pipeline")

    def test_partner_text_node_exposes_normal_controls_without_credentials(self):
        inputs = QwenImage3TextToImage.INPUT_TYPES()
        exposed_names = set(inputs["required"]) | set(inputs.get("optional", {}))

        self.assertEqual(
            exposed_names,
            {
                "provider",
                "model",
                "prompt",
                "negative_prompt",
                "width",
                "height",
                "count",
                "seed",
                "prompt_extend",
                "watermark",
            },
        )
        self.assertNotIn("api_key", exposed_names)
        self.assertEqual(
            QwenImage3TextToImage.RETURN_NAMES,
            ("images", "edit_brief_json", "run_metadata"),
        )

    def test_partner_edit_node_exposes_three_ordered_reference_sockets(self):
        inputs = QwenImage3Edit.INPUT_TYPES()

        self.assertIn("image_1", inputs["required"])
        self.assertEqual(list(inputs["optional"]), ["image_2", "image_3"])
        self.assertIn("size_mode", inputs["required"])
        self.assertEqual(
            QwenImage3Edit.RETURN_NAMES,
            ("images", "edit_brief_json", "run_metadata"),
        )

    def test_partner_node_rejects_an_unsupported_control_before_loading_a_key(self):
        with self.assertRaisesRegex(
            ValueError, "OpenRouter does not support negative_prompt"
        ):
            QwenImage3TextToImage().render(
                provider="openrouter",
                model="qwen-image-3.0-pro",
                prompt="A monochrome interface.",
                negative_prompt="no gradients",
                width=1024,
                height=1024,
                count=1,
                seed=42,
                prompt_extend=False,
                watermark=False,
            )

    def test_partner_edit_rejects_a_batch_on_one_visible_role(self):
        with self.assertRaisesRegex(ValueError, "visible @ImageN roles ambiguous"):
            QwenImage3Edit().render(
                provider="openrouter",
                model="qwen-image-3.0-pro",
                prompt="Edit @Image1.",
                negative_prompt="",
                width=1024,
                height=1024,
                count=1,
                seed=42,
                prompt_extend=False,
                watermark=False,
                size_mode="custom",
                image_1=[object(), object()],
            )

    def test_partner_edit_rejects_a_gap_between_visible_roles(self):
        with self.assertRaisesRegex(ValueError, "image_3 requires image_2"):
            QwenImage3Edit().render(
                provider="openrouter",
                model="qwen-image-3.0-pro",
                prompt="Edit @Image1 using @Image3.",
                negative_prompt="",
                width=1024,
                height=1024,
                count=1,
                seed=42,
                prompt_extend=False,
                watermark=False,
                size_mode="custom",
                image_1=[object()],
                image_3=[object()],
            )

    def test_partner_run_metadata_records_hashes_counts_and_provider_identity(self):
        response = {
            "id": "request-32",
            "data": [{"b64_json": "aW1hZ2U=", "media_type": "image/png"}],
            "usage": {"cost": 0.04},
        }
        result = ProviderResult(
            provider="openrouter",
            request={"model": "qwen/qwen-image-3-pro"},
            response=response,
        )
        brief = {
            "provider": "openrouter",
            "model": "qwen/qwen-image-3-pro",
            "objective": "Edit Image 1.",
            "output": {"count": 1, "seed": 42},
        }
        references = [
            {
                "role": "image_1",
                "width": 1024,
                "height": 1024,
                "sha256": "reference-hash",
                "data_url": "data:image/png;base64,AAAA",
            }
        ]

        with (
            patch(
                "qwen_ui_pipeline.comfyui_node._provider_clients",
                return_value=(object(), None),
            ),
            patch(
                "qwen_ui_pipeline.comfyui_node.generate_with_provider",
                return_value=result,
            ),
            patch(
                "qwen_ui_pipeline.comfyui_node._response_tensors",
                return_value="image-batch",
            ),
        ):
            images, edit_brief_json, run_metadata = _partner_render(brief, references)

        metadata = json.loads(run_metadata)
        self.assertEqual(images, "image-batch")
        self.assertEqual(json.loads(edit_brief_json), brief)
        self.assertEqual(metadata["provider"], "openrouter")
        self.assertEqual(metadata["request_id"], "request-32")
        self.assertEqual(metadata["requested_output_count"], 1)
        self.assertEqual(metadata["completed_output_count"], 1)
        self.assertEqual(metadata["references"][0]["sha256"], "reference-hash")
        self.assertTrue(metadata["output_sha256"][0].startswith("6105d6cc76af4003"))

    def test_region_composite_exposes_only_images_and_explicit_coordinates(self):
        inputs = ReferenceRegionComposite.INPUT_TYPES()
        exposed_names = set(inputs["required"])

        self.assertEqual(
            exposed_names,
            {"reference_images", "generated_images", "region"},
        )
        self.assertEqual(ReferenceRegionComposite.RETURN_TYPES, ("IMAGE",))


if __name__ == "__main__":
    unittest.main()
