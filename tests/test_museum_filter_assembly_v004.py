from __future__ import annotations

import unittest
from pathlib import Path

try:
    from PIL import Image, ImageChops

    HAVE_PIL = True
except ImportError:
    HAVE_PIL = False

if HAVE_PIL:
    from scripts import assemble_museum_filter_v004 as assembly


ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(HAVE_PIL, "Pillow is not installed")
class ThreeRegionMuseumFilterAssemblyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.baseline = Image.open(
            ROOT / "artifacts/runs/museum-filter-assembly-v001/assembly-v001-native.png"
        ).convert("RGB")
        cls.output, cls.declared = assembly.assemble_native(cls.baseline)
        cls.actual = assembly.changed_pixel_mask(cls.baseline, cls.output)

    def test_actual_changes_are_inside_only_three_declared_regions(self) -> None:
        self.assertEqual(self.actual.tobytes(), self.declared.tobytes())
        outside = ImageChops.multiply(self.actual, ImageChops.invert(self.declared))
        self.assertIsNone(outside.getbbox())

        allowed = Image.new("L", self.baseline.size, 0)
        for box in assembly.EDIT_BOXES:
            allowed.paste(255, box)
        outside_boxes = ImageChops.multiply(self.actual, ImageChops.invert(allowed))
        self.assertIsNone(outside_boxes.getbbox())

        for box in assembly.EDIT_BOXES:
            self.assertIsNotNone(self.actual.crop(box).getbbox(), box)

    def test_all_unmarked_english_and_controls_are_v001_pixels(self) -> None:
        # The title copy starts at x=20; only its neighboring bead is repaired.
        self.assertEqual(
            self.baseline.crop((20, 3, 160, 23)).tobytes(),
            self.output.crop((20, 3, 160, 23)).tobytes(),
        )
        # The active object tab and the complete body are frozen to v001.
        self.assertEqual(
            self.baseline.crop((3, 23, 21, 69)).tobytes(),
            self.output.crop((3, 23, 21, 69)).tobytes(),
        )
        self.assertEqual(
            self.baseline.crop((19, 23, 310, 208)).tobytes(),
            self.output.crop((19, 23, 310, 208)).tobytes(),
        )

    def test_bead_and_close_backgrounds_return_to_the_v001_glass(self) -> None:
        bar = assembly.header_bar()
        for box, foreground in (
            (assembly.LEFT_BEAD_BOX, assembly.bead_mask()),
            (assembly.RIGHT_BEAD_BOX, assembly.bead_mask()),
            (assembly.CLOSE_BOX, assembly.close_mask()),
        ):
            local = (box[0] - 3, box[1] - 3, box[2] - 3, box[3] - 3)
            expected = bar.crop(local)
            actual = self.output.crop(box)
            background = ImageChops.invert(foreground)
            self.assertIsNone(
                ImageChops.multiply(
                    ImageChops.difference(expected, actual).convert("L"),
                    background,
                ).getbbox(),
                box,
            )

    def test_material_copy_is_preserved_inside_a_stepped_tab(self) -> None:
        baseline_pixels = self.baseline.load()
        output_pixels = self.output.load()
        ink = assembly.TAB_OFF_INK
        ink_points = [
            (x, y)
            for y in range(assembly.MATERIAL_BOX[1], assembly.MATERIAL_BOX[3])
            for x in range(assembly.MATERIAL_BOX[0], assembly.MATERIAL_BOX[2])
            if baseline_pixels[x, y] == ink
        ]
        self.assertGreater(len(ink_points), 50)
        for point in ink_points:
            self.assertEqual(output_pixels[point], ink)

        shape = assembly.material_tab_mask()
        self.assertEqual(shape.getpixel((15, 0)), 0)
        self.assertEqual(shape.getpixel((15, 10)), 255)
        self.assertEqual(shape.getpixel((15, 54)), 0)


if __name__ == "__main__":
    unittest.main()
