import json
import tempfile
import unittest
from pathlib import Path

from qwen_ui_pipeline.cli import main


class RecordComfyRunTests(unittest.TestCase):
    def test_writes_component_assembly_workflow_from_layout(self):
        layout = {
            "donor_normalization": {
                "width": 1572,
                "height": 718,
                "upscale_method": "nearest-exact",
                "crop": "disabled",
            },
            "cleanplate": {
                "source_region": [185, 235, 1245, 65],
                "target_region": [185, 130, 1245, 350],
            },
            "components": [
                {
                    "source_region": [185, 355, 1245, 130],
                    "target": [185, 280],
                }
            ],
            "final_edit_region": [160, 130, 1350, 350],
        }

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            layout_path = root / "layout.json"
            layout_path.write_text(json.dumps(layout), encoding="utf-8")
            output = root / "workflow.json"

            status = main(
                [
                    "component-assembly-workflow",
                    str(layout_path),
                    "--reference-filename",
                    "reference.png",
                    "--generated-filename",
                    "donor.png",
                    "--filename-prefix",
                    "component-test",
                    "--preserve-reference-alpha",
                    "--output",
                    str(output),
                ]
            )

            self.assertEqual(status, 0)
            workflow = json.loads(output.read_text(encoding="utf-8"))
            final_composite = next(
                node
                for node in workflow.values()
                if node["class_type"] == "ReferenceRegionComposite"
            )
            self.assertEqual(final_composite["inputs"]["reference_masks"], ["1", 1])

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
