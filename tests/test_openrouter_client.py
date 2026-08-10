import json
import tempfile
import unittest
import urllib.error
from io import BytesIO
from pathlib import Path

from qwen_ui_pipeline import OpenRouterImageClient, write_run_artifacts


class _Response:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return json.dumps(self.payload).encode()


class OpenRouterImageClientTests(unittest.TestCase):
    def test_posts_an_authenticated_image_request_and_returns_response(self):
        captured = {}

        def open_request(request, *, timeout):
            captured["authorization"] = request.get_header("Authorization")
            captured["body"] = json.loads(request.data)
            captured["timeout"] = timeout
            return _Response(
            {
                "data": [{"b64_json": "aW1hZ2U=", "media_type": "image/png"}],
                "usage": {"cost": 0.04},
            }
            )

        client = OpenRouterImageClient("test-key", opener=open_request)
        response = client.generate({"model": "qwen/qwen-image-3-pro", "prompt": "golf"})

        self.assertEqual(captured["authorization"], "Bearer test-key")
        self.assertEqual(captured["body"]["prompt"], "golf")
        self.assertEqual(response["usage"]["cost"], 0.04)

    def test_writes_reproducible_artifacts_without_copying_base64_into_metadata(self):
        response = {
            "data": [{"b64_json": "aW1hZ2U=", "media_type": "image/png"}],
            "usage": {"cost": 0.04},
        }
        request = {"model": "qwen/qwen-image-3-pro", "prompt": "golf"}
        brief = {"objective": "Replace the flower with a golf club."}

        with tempfile.TemporaryDirectory() as directory:
            record = write_run_artifacts(Path(directory), brief, request, response)

            self.assertEqual((Path(directory) / "image-01.png").read_bytes(), b"image")
            metadata = (Path(directory) / "response.json").read_text()
            self.assertNotIn("aW1hZ2U=", metadata)
            self.assertTrue(record["outputs"][0]["sha256"].startswith("6105d6cc76af4003"))

    def test_surfaces_a_provider_error_message_without_exposing_the_key(self):
        def fail_request(request, *, timeout):
            raise urllib.error.HTTPError(
                request.full_url,
                404,
                "Not Found",
                {},
                BytesIO(b'{"error":{"message":"No endpoints found for this model"}}'),
            )

        client = OpenRouterImageClient("never-print-this-key", opener=fail_request)

        with self.assertRaisesRegex(RuntimeError, "No endpoints found for this model") as raised:
            client.generate({"model": "qwen/qwen-image-3-pro", "prompt": "golf"})
        self.assertNotIn("never-print-this-key", str(raised.exception))

    def test_redacts_nested_alibaba_reference_data_from_run_metadata(self):
        request = {
            "model": "qwen-image-3.0-pro",
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"image": "data:image/png;base64,SECRET-BYTES"},
                            {"text": "golf"},
                        ],
                    }
                ]
            },
        }
        response = {
            "data": [{"b64_json": "aW1hZ2U=", "media_type": "image/png"}],
        }

        with tempfile.TemporaryDirectory() as directory:
            write_run_artifacts(Path(directory), {}, request, response)

            metadata = (Path(directory) / "request.json").read_text()
            self.assertNotIn("SECRET-BYTES", metadata)
            self.assertIn("[recorded separately]", metadata)

    def test_records_alibaba_prompt_and_external_provenance(self):
        request = {
            "model": "qwen-image-3.0-pro",
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [{"text": "SURGICAL GOLF EDIT"}],
                    }
                ]
            },
        }
        response = {
            "data": [{"b64_json": "aW1hZ2U=", "media_type": "image/png"}],
        }

        with tempfile.TemporaryDirectory() as directory:
            write_run_artifacts(
                Path(directory),
                {},
                request,
                response,
                provenance={"provider": "alibaba", "prompt_id": "prompt-123"},
            )

            self.assertEqual(
                (Path(directory) / "prompt.txt").read_text(),
                "SURGICAL GOLF EDIT\n",
            )
            run = json.loads((Path(directory) / "run.json").read_text())
            self.assertEqual(run["provenance"]["provider"], "alibaba")
            self.assertEqual(run["provenance"]["prompt_id"], "prompt-123")


if __name__ == "__main__":
    unittest.main()
