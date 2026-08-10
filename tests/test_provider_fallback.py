import unittest

from qwen_ui_pipeline import generate_with_provider


class _BlockedOpenRouter:
    def generate(self, _request):
        raise RuntimeError(
            "OpenRouter Image API returned HTTP 404: No endpoints available matching "
            "your guardrail restrictions and data policy"
        )


class _WorkingAlibaba:
    def __init__(self):
        self.request = None

    def generate(self, request):
        self.request = request
        return {"data": [{"b64_json": "aW1hZ2U=", "media_type": "image/png"}]}


class ProviderFallbackTests(unittest.TestCase):
    def test_auto_falls_back_only_for_openrouter_privacy_guardrail_block(self):
        alibaba = _WorkingAlibaba()
        brief = {
            "provider": "auto",
            "objective": "Replace the flower with a golf club.",
            "output": {"resolution": "1K", "aspect_ratio": "4:3", "count": 1},
        }

        result = generate_with_provider(
            brief,
            reference_urls=["data:image/png;base64,AAAA"],
            openrouter_client=_BlockedOpenRouter(),
            alibaba_client=alibaba,
        )

        self.assertEqual(result.provider, "alibaba")
        self.assertEqual(alibaba.request["model"], "qwen-image-3.0-pro")


if __name__ == "__main__":
    unittest.main()
