import json
import tempfile
import unittest
from pathlib import Path

from qwen_ui_pipeline.cli import main


class RecordComfyRunTests(unittest.TestCase):
    def test_writes_mask_owned_sticker_workflow(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "sticker-mask.api.json"

            status = main(
                [
                    "mask-assembly-workflow",
                    "--reference-filename",
                    "device.png",
                    "--artwork-filename",
                    "sticker.png",
                    "--mask-filename",
                    "sticker-mask.png",
                    "--integration-filename",
                    "contact-donor.png",
                    "--canvas-width",
                    "1024",
                    "--canvas-height",
                    "768",
                    "--target-quad",
                    "120,90,430,72,448,350,105,366",
                    "--filename-prefix",
                    "stickers/mask-owned/v001",
                    "--output",
                    str(output),
                ]
            )

            self.assertEqual(status, 0)
            workflow = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(workflow["4"]["class_type"], "StickerPerspectiveWarp")
            self.assertEqual(workflow["11"]["class_type"], "MaskedReferenceFidelityGate")
            self.assertEqual(workflow["13"]["class_type"], "SaveImage")

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
