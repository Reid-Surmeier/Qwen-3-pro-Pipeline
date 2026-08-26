import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageChops

from scripts.build_issue2_e_selection_fixture import build_fixture


REFERENCE = Path(
    "artifacts/issue-2/useful-edit/source/intel-inside-celeron-crop.png"
)
SOURCE_EXPORT = Path(
    "artifacts/issue-2/useful-edit/source/intel-inside-source-node-67-710.png"
)


class Issue2ESelectionFixtureTests(unittest.TestCase):
    def test_selects_final_e_and_places_target_inside_lower_blue_band(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory)
            manifest = build_fixture(REFERENCE, SOURCE_EXPORT, output)

            self.assertEqual(
                manifest["selection"]["source_letter_box"], [587, 263, 635, 314]
            )
            self.assertEqual(
                manifest["selection"]["target_letter_box"], [360, 640, 408, 691]
            )
            self.assertEqual(manifest["selection"]["source_letter_pixels"], 1701)
            self.assertEqual(manifest["selection"]["target_letter_pixels"], 1701)
            self.assertGreaterEqual(
                manifest["selection"]["target_letter_box"][1], 600
            )
            self.assertEqual(
                manifest["reference"]["sha256"],
                "7c8e8767f72b72ce4fa4c888507f5ad060003a6cab7802f3e0deef44c8de35d7",
            )
            self.assertEqual(manifest["source_export"]["figjam_node_id"], "67:710")

            with Image.open(output / "source-region-mask-v001.png") as source:
                source_mask = source.convert("L")
            with Image.open(output / "target-region-mask-v001.png") as target:
                target_mask = target.convert("L")
            with Image.open(output / "combined-region-mask-v001.png") as combined:
                combined_mask = combined.convert("L")
            self.assertIsNone(ImageChops.multiply(source_mask, target_mask).getbbox())
            expected_pixels = sum(source_mask.histogram()[1:]) + sum(
                target_mask.histogram()[1:]
            )
            self.assertEqual(
                sum(combined_mask.histogram()[1:]), expected_pixels
            )

            with Image.open(output / "green-selection-key-v001.png") as key:
                colors = set(key.convert("RGB").getcolors(maxcolors=3) or [])
            self.assertEqual(
                {color for _, color in colors}, {(0, 0, 0), (0, 255, 0)}
            )


if __name__ == "__main__":
    unittest.main()
