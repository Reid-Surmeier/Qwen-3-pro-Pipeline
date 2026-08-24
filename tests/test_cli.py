import json
import hashlib
import tempfile
import unittest
from pathlib import Path

from qwen_ui_pipeline.cli import main
from qwen_ui_pipeline import WorkflowContractError


def strict_brief() -> dict:
    return {
        "workflow_profile": "qwen-source-locked-single-decision-v1",
        "runtime": "comfyui",
        "provider": "alibaba",
        "model": "qwen/qwen-image-3-pro",
        "stage": {
            "id": "01-object",
            "decision": "Replace only the flower.",
            "status": "rendered",
        },
        "reference": {
            "path": "reference.png",
            "sha256": hashlib.sha256(b"reference").hexdigest(),
        },
        "objective": "Replace the flower with a golf club.",
        "reference_role": "The reference is immutable outside the selected flower.",
        "preservation_invariants": ["Keep all surrounding pixels."],
        "canvas": ["Preserve source geometry."],
        "regions": [
            {
                "name": "selected flower",
                "bounds": [10, 20, 30, 40],
                "change": "Replace only the flower.",
            }
        ],
        "style": ["Match the source raster style."],
        "negative_constraints": ["No global redraw."],
        "quality_checks": ["Outside-region pixels remain unchanged."],
        "output": {
            "resolution": "1K",
            "aspect_ratio": "source",
            "size": "948*806",
            "count": 4,
            "seed": 1786,
        },
    }


class RecordComfyRunTests(unittest.TestCase):
    def test_records_existing_comfy_outputs_with_provider_provenance(self):
        brief = strict_brief()

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            brief_path = root / "brief.json"
            brief_path.write_text(json.dumps(brief), encoding="utf-8")
            reference = root / "reference.png"
            reference.write_bytes(b"reference")
            images = []
            for index in range(4):
                image = root / f"result-{index + 1}.png"
                image.write_bytes(f"result-{index + 1}".encode())
                images.append(image)
            output = root / "run"

            status = main(
                [
                    "record-comfy",
                    str(brief_path),
                    "--provider",
                    "alibaba",
                    "--reference",
                    str(reference),
                    *[
                        argument
                        for image in images
                        for argument in ("--image", str(image))
                    ],
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
            self.assertEqual((output / "image-01.png").read_bytes(), b"result-1")
            run = json.loads((output / "run.json").read_text())
            self.assertEqual(len(run["outputs"]), 4)
            self.assertEqual(run["provenance"]["provider"], "alibaba")
            self.assertEqual(run["provenance"]["prompt_id"], "prompt-123")
            self.assertEqual(run["provenance"]["figma_file_key"], "figma-key")
            self.assertEqual(len(run["provenance"]["reference_sha256"]), 64)

    def test_rejects_direct_provider_generation(self):
        with tempfile.TemporaryDirectory() as directory:
            brief_path = Path(directory) / "brief.json"
            brief_path.write_text(json.dumps(strict_brief()), encoding="utf-8")

            with self.assertRaisesRegex(
                WorkflowContractError, "direct provider generation is disabled"
            ):
                main(["generate", str(brief_path)])


if __name__ == "__main__":
    unittest.main()
