import unittest

from qwen_ui_pipeline.providers.vision import OpenRouterVisionClient, _encode, _strip_fence
from qwen_ui_pipeline.verifier import RegionReview


class Solid:
    """A minimal stand-in for a PIL image crop."""

    def __init__(self, width=4, height=3):
        self.width = width
        self.height = height
        self.resized_to = None

    def convert(self, mode):
        return self

    def resize(self, size, resample):
        self.resized_to = size
        return Solid(*size)

    def save(self, buffer, format):
        buffer.write(b"\x89PNG\r\n\x1a\n" + bytes(self.width * self.height))


class ReviewerIndependenceTests(unittest.TestCase):
    def test_refuses_to_review_with_the_builder_family(self):
        with self.assertRaises(ValueError) as raised:
            OpenRouterVisionClient(api_key="k", model="qwen/qwen-image-3-pro")

        self.assertIn("independent model family", str(raised.exception))

    def test_requires_a_key(self):
        with self.assertRaises(ValueError):
            OpenRouterVisionClient(api_key="")

    def test_defaults_to_a_non_builder_reviewer(self):
        self.assertFalse(OpenRouterVisionClient(api_key="k").model.startswith("qwen/"))


class MagnificationTests(unittest.TestCase):
    def test_magnifies_a_crop_with_nearest_neighbour(self):
        crop = Solid(10, 4)

        _encode(crop, scale=4)

        self.assertEqual(crop.resized_to, (40, 16))

    def test_leaves_a_crop_untouched_at_unit_scale(self):
        crop = Solid(10, 4)

        _encode(crop, scale=1)

        self.assertIsNone(crop.resized_to)


class FenceStrippingTests(unittest.TestCase):
    def test_unwraps_a_fenced_verdict(self):
        self.assertEqual(_strip_fence('```json\n{"verdict": "match"}\n```'), '{"verdict": "match"}')

    def test_leaves_a_bare_verdict_alone(self):
        self.assertEqual(_strip_fence('{"verdict": "match"}'), '{"verdict": "match"}')


class PromptTests(unittest.TestCase):
    def test_includes_the_licensed_intent_in_the_request(self):
        captured = {}

        def opener(request, timeout):
            captured["body"] = request.data.decode("utf-8")

            class Response:
                def __enter__(self_inner):
                    return self_inner

                def __exit__(self_inner, *args):
                    return False

                def read(self_inner):
                    return b'{"choices":[{"message":{"content":"{\\"verdict\\":\\"match\\"}"}}]}'

            return Response()

        client = OpenRouterVisionClient(api_key="k", _opener=opener)
        client.review(
            RegionReview(
                region="title",
                baseline_crop=Solid(),
                candidate_crop=Solid(),
                intent="replace the numeral 11 with 24",
            )
        )

        self.assertIn("replace the numeral 11 with 24", captured["body"])
        self.assertIn("Do not report the licensed change itself as a defect", captured["body"])


if __name__ == "__main__":
    unittest.main()
