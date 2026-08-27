import unittest

from qwen_ui_pipeline.partner_controls import (
    build_partner_edit_brief,
    build_partner_text_brief,
    resolve_image_references,
)
from qwen_ui_pipeline.providers.router import generate_with_provider


class _CapturingClient:
    def __init__(self):
        self.requests = []

    def generate(self, request):
        self.requests.append(request)
        return {"data": [{"b64_json": "aW1hZ2U=", "media_type": "image/png"}]}


class PartnerControlsTests(unittest.TestCase):
    def test_resolves_ordered_image_references_without_rewriting_email_addresses(self):
        prompt = "Use @Image3 with @image and @IMAGE2; keep user@image1.com unchanged."

        self.assertEqual(
            resolve_image_references(prompt, 3),
            "Use Image 3 with Image 1 and Image 2; keep user@image1.com unchanged.",
        )

    def test_rejects_a_reference_that_is_not_visibly_connected(self):
        with self.assertRaisesRegex(ValueError, "only 2 reference images"):
            resolve_image_references("Combine @Image1 and @Image3", 2)

    def test_builds_an_alibaba_edit_brief_with_explicit_partner_controls(self):
        brief = build_partner_edit_brief(
            provider="alibaba",
            model="qwen-image-3.0-pro",
            prompt="Transfer @Image2 onto @Image1.",
            negative_prompt="no extra controls",
            size_mode="match input",
            width=1024,
            height=1024,
            count=3,
            seed=42,
            prompt_extend=True,
            watermark=True,
            reference_dimensions=[(948, 806), (512, 512)],
        )

        self.assertEqual(brief["provider"], "alibaba")
        self.assertEqual(brief["objective"], "Transfer Image 2 onto Image 1.")
        self.assertEqual(brief["negative_prompt"], "no extra controls")
        self.assertEqual(brief["output"]["size"], "948*806")
        self.assertEqual(brief["output"]["count"], 3)
        self.assertTrue(brief["output"]["prompt_extend"])
        self.assertTrue(brief["output"]["watermark"])

    def test_openrouter_rejects_unsupported_paid_controls_before_submission(self):
        for option in ("negative_prompt", "prompt_extend", "watermark"):
            controls = {
                "negative_prompt": "",
                "prompt_extend": False,
                "watermark": False,
            }
            controls[option] = "no gradients" if option == "negative_prompt" else True
            with self.subTest(option=option), self.assertRaisesRegex(
                ValueError, f"OpenRouter does not support {option}"
            ):
                build_partner_text_brief(
                    provider="openrouter",
                    model="qwen/qwen-image-3-pro",
                    prompt="A monochrome interface.",
                    width=1024,
                    height=1024,
                    count=1,
                    seed=42,
                    **controls,
                )

    def test_rejects_count_and_seed_outside_the_partner_contract(self):
        for field, value, expected in (
            ("count", 7, "Output count must be between 1 and 6"),
            ("seed", -1, "Seed must be between 0"),
        ):
            controls = {"count": 1, "seed": 42}
            controls[field] = value
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, expected):
                build_partner_text_brief(
                    provider="openrouter",
                    model="qwen-image-3.0-pro",
                    prompt="A monochrome interface.",
                    negative_prompt="",
                    width=1024,
                    height=1024,
                    prompt_extend=False,
                    watermark=False,
                    **controls,
                )

    def test_maps_supported_openrouter_dimensions_to_resolution_and_aspect(self):
        brief = build_partner_text_brief(
            provider="openrouter",
            model="qwen/qwen-image-3-pro",
            prompt="A monochrome interface.",
            negative_prompt="",
            width=1024,
            height=1024,
            count=1,
            seed=42,
            prompt_extend=False,
            watermark=False,
        )

        self.assertEqual(brief["output"]["resolution"], "1K")
        self.assertEqual(brief["output"]["aspect_ratio"], "1:1")

    def test_rejects_openrouter_dimensions_that_cannot_be_represented_exactly(self):
        with self.assertRaisesRegex(ValueError, "supported OpenRouter size"):
            build_partner_text_brief(
                provider="openrouter",
                model="qwen/qwen-image-3-pro",
                prompt="A monochrome interface.",
                negative_prompt="",
                width=948,
                height=806,
                count=1,
                seed=42,
                prompt_extend=False,
                watermark=False,
            )

    def test_rejects_more_than_three_portable_edit_references(self):
        with self.assertRaisesRegex(ValueError, "maximum of 3"):
            build_partner_edit_brief(
                provider="alibaba",
                model="qwen-image-3.0-pro",
                prompt="Combine the references.",
                negative_prompt="",
                size_mode="auto",
                width=1024,
                height=1024,
                count=1,
                seed=42,
                prompt_extend=True,
                watermark=False,
                reference_dimensions=[(512, 512)] * 4,
            )

    def test_same_three_reference_controls_build_both_provider_requests(self):
        references = [f"data:image/png;base64,{index}" for index in range(1, 4)]
        common = {
            "model": "qwen-image-3.0-pro",
            "prompt": "Use @Image1 layout, @Image2 style, and @Image3 asset.",
            "negative_prompt": "",
            "size_mode": "custom",
            "width": 1024,
            "height": 1024,
            "count": 1,
            "seed": 42,
            "prompt_extend": False,
            "watermark": False,
            "reference_dimensions": [(1024, 1024)] * 3,
        }
        openrouter = _CapturingClient()
        alibaba = _CapturingClient()

        openrouter_result = generate_with_provider(
            build_partner_edit_brief(provider="openrouter", **common),
            reference_urls=references,
            openrouter_client=openrouter,
        )
        alibaba_result = generate_with_provider(
            build_partner_edit_brief(provider="alibaba", **common),
            reference_urls=references,
            alibaba_client=alibaba,
        )

        self.assertEqual(openrouter_result.provider, "openrouter")
        self.assertEqual(alibaba_result.provider, "alibaba")
        self.assertEqual(len(openrouter.requests[0]["input_references"]), 3)
        alibaba_content = alibaba.requests[0]["input"]["messages"][0]["content"]
        self.assertEqual([item["image"] for item in alibaba_content[:3]], references)
        self.assertIn("Image 3", openrouter.requests[0]["prompt"])
        self.assertIn("Image 3", alibaba_content[-1]["text"])


if __name__ == "__main__":
    unittest.main()
