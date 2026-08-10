import json
import tempfile
import unittest
from pathlib import Path

from qwen_ui_pipeline.cli import main


class RecordComfyRunTests(unittest.TestCase):
    def test_records_existing_comfy_outputs_with_provider_provenance(self):
        brief = {
            "objective": "Replace the flower with a golf club.",
            "output": {
                "resolution": "1K",
                "aspect_ratio": "source",
                "size": "948*806",
                "count": 1,
            },
        }

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            brief_path = root / "brief.json"
            brief_path.write_text(json.dumps(brief), encoding="utf-8")
            reference = root / "reference.png"
            reference.write_bytes(b"reference")
            image = root / "result.png"
            image.write_bytes(b"result")
            output = root / "run"

            status = main(
                [
                    "record-comfy",
                    str(brief_path),
                    "--provider",
                    "alibaba",
                    "--reference",
                    str(reference),
                    "--image",
                    str(image),
                    "--output-dir",
                    str(output),
                    "--prompt-id",
                    "prompt-123",
                    "--source-url",
                    "https://example.com/reference.png",
                    "--figma-file-key",
                    "figma-key",
                ]
            )

            self.assertEqual(status, 0)
            self.assertEqual((output / "image-01.png").read_bytes(), b"result")
            run = json.loads((output / "run.json").read_text())
            self.assertEqual(run["provenance"]["provider"], "alibaba")
            self.assertEqual(run["provenance"]["prompt_id"], "prompt-123")
            self.assertEqual(run["provenance"]["figma_file_key"], "figma-key")
            self.assertEqual(len(run["provenance"]["reference_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
