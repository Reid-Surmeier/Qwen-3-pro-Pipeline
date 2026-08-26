import tempfile
import unittest
from pathlib import Path

from PIL import Image

from scripts.evaluate_issue2_qualification import evaluate_qualification


class Issue2QualificationEvaluationTests(unittest.TestCase):
    def test_records_mask_geometry_and_multibackground_evidence(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            reference = Image.new("RGBA", (5, 5), (255, 255, 255, 0))
            for y in range(1, 4):
                for x in range(1, 4):
                    reference.putpixel((x, y), (12, 80, 160, 255))
            mask = Image.new("LA", (5, 5), (0, 0))
            for y in range(1, 4):
                for x in range(1, 4):
                    mask.putpixel((x, y), (255, 255))
            output = Image.new("RGB", (5, 5), (0, 0, 0))
            output.paste(reference.convert("RGB"), mask=mask.getchannel("L"))
            reference_path = root / "reference.png"
            mask_path = root / "mask.png"
            custom_path = root / "custom.png"
            core_path = root / "core.png"
            custom_mask_path = root / "custom-mask.png"
            custom_cutout_path = root / "custom-cutout.png"
            core_cutout_path = root / "core-cutout.png"
            sheet_path = root / "sheet.png"
            reference.save(reference_path)
            mask.save(mask_path)
            output.save(custom_path)
            output.save(core_path)
            mask.convert("RGB").save(custom_mask_path)

            report = evaluate_qualification(
                reference_path=reference_path,
                mask_path=mask_path,
                custom_mask_path=custom_mask_path,
                custom_output_path=custom_path,
                core_output_path=core_path,
                custom_cutout_path=custom_cutout_path,
                core_cutout_path=core_cutout_path,
                contact_sheet_path=sheet_path,
            )

            self.assertEqual(report["custom_path"]["false_opaque_pixels"], 0)
            self.assertEqual(report["custom_path"]["false_transparent_pixels"], 0)
            self.assertEqual(report["custom_path"]["silhouette_iou"], 1.0)
            self.assertEqual(report["custom_path"]["centroid_drift_px"], 0.0)
            self.assertEqual(report["custom_path"]["scale_drift"], 0.0)
            self.assertEqual(
                report["custom_path"]["boundary_error_fraction"], 0.0
            )
            self.assertEqual(report["custom_vs_core_changed_rgb_pixels"], 0)
            with Image.open(custom_cutout_path) as cutout:
                self.assertEqual(cutout.mode, "RGBA")
                self.assertEqual(cutout.getchannel("A").getextrema(), (0, 255))
            with Image.open(core_cutout_path) as cutout:
                self.assertEqual(cutout.mode, "RGBA")
            self.assertTrue(sheet_path.is_file())


if __name__ == "__main__":
    unittest.main()
