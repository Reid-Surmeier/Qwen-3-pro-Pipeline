import tempfile
import unittest
from pathlib import Path

from PIL import Image

from scripts.evaluate_issue2_mask_outputs import measure_image


class Issue2MaskEvaluationTests(unittest.TestCase):
    def test_measures_background_and_subject_without_treating_near_green_as_artwork(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "fixture.png"
            image = Image.new("RGB", (10, 10), (0, 255, 0))
            for y in range(3, 7):
                for x in range(2, 8):
                    image.putpixel((x, y), (255, 255, 255))
            image.save(path)

            result = measure_image(path, border_width=1)

        self.assertEqual(result["width"], 10)
        self.assertEqual(result["height"], 10)
        self.assertEqual(result["subject_bbox"], [2, 3, 8, 7])
        self.assertAlmostEqual(result["subject_fraction"], 0.24)
        self.assertEqual(result["border_near_green_fraction"], 1.0)
        self.assertEqual(result["border_mean_absolute_error_to_00ff00"], 0.0)


if __name__ == "__main__":
    unittest.main()
