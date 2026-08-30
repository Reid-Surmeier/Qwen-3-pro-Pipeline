from __future__ import annotations

import unittest
from pathlib import Path

try:
    from PIL import Image, ImageChops
    HAVE_PIL = True
except ImportError:
    HAVE_PIL = False

if HAVE_PIL:
    from scripts import assemble_museum_filter_v005 as assembly


ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(HAVE_PIL, "Pillow is not installed")
class ThreeRegionMuseumFilterAssemblyV005Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.baseline = Image.open(
            ROOT
            / "artifacts/runs/museum-filter-assembly-v001/assembly-v001-native.png"
        ).convert("RGB")
        cls.output, cls.declared = assembly.assemble_native(cls.baseline)
        cls.actual = assembly.changed_pixel_mask(cls.baseline, cls.output)

    def test_declared_mask_is_exactly_the_real_three_region_difference(self) -> None:
        self.assertEqual(self.actual.tobytes(), self.declared.tobytes())
        allowed = Image.new("L", self.baseline.size, 0)
        for box in assembly.EDIT_BOXES:
            allowed.paste(255, box)
            self.assertIsNotNone(self.actual.crop(box).getbbox(), box)
        outside = ImageChops.multiply(self.actual, ImageChops.invert(allowed))
        self.assertIsNone(outside.getbbox())

    def test_unmarked_text_and_controls_are_v001_pixels(self) -> None:
        self.assertEqual(
            self.baseline.crop((20, 3, 160, 23)).tobytes(),
            self.output.crop((20, 3, 160, 23)).tobytes(),
        )
        self.assertEqual(
            self.baseline.crop((3, 23, 21, 69)).tobytes(),
            self.output.crop((3, 23, 21, 69)).tobytes(),
        )
        self.assertEqual(
            self.baseline.crop((23, 23, 310, 208)).tobytes(),
            self.output.crop((23, 23, 310, 208)).tobytes(),
        )

    def test_beads_have_padding_on_all_four_sides(self) -> None:
        _, alpha = assembly.bead_asset()
        self.assertIsNotNone(alpha.getbbox())
        for x in range(alpha.width):
            self.assertEqual(alpha.getpixel((x, 0)), 0)
            self.assertEqual(alpha.getpixel((x, alpha.height - 1)), 0)
        for y in range(alpha.height):
            self.assertEqual(alpha.getpixel((0, y)), 0)
            self.assertEqual(alpha.getpixel((alpha.width - 1, y)), 0)

    def test_tab_stairs_are_reversed_and_tab_is_wider(self) -> None:
        shape = assembly.material_tab_mask()
        self.assertEqual(shape.size, (20, 55))
        self.assertEqual(shape.getpixel((19, 0)), 255)
        self.assertEqual(shape.getpixel((19, 10)), 0)
        self.assertEqual(shape.getpixel((19, 54)), 255)

    def test_material_copy_is_preserved_with_space_before_the_edge(self) -> None:
        baseline_pixels = self.baseline.load()
        output_pixels = self.output.load()
        ink_points = [
            (x, y)
            for y in range(assembly.MATERIAL_INK_BOX[1], assembly.MATERIAL_INK_BOX[3])
            for x in range(assembly.MATERIAL_INK_BOX[0], assembly.MATERIAL_INK_BOX[2])
            if baseline_pixels[x, y] == assembly.TAB_OFF_INK
        ]
        self.assertGreater(len(ink_points), 50)
        shifted_points = [
            (
                x + assembly.MATERIAL_TEXT_SHIFT[0],
                y + assembly.MATERIAL_TEXT_SHIFT[1],
            )
            for x, y in ink_points
        ]
        for point in shifted_points:
            self.assertEqual(output_pixels[point], assembly.TAB_OFF_INK)

        local_rightmost_ink = max(x for x, _ in shifted_points) - assembly.MATERIAL_BOX[0]
        middle_y = assembly.MATERIAL_BOX[3] - assembly.MATERIAL_BOX[1]
        middle_y //= 2
        shape = assembly.material_tab_mask()
        local_edge = max(x for x in range(shape.width) if shape.getpixel((x, middle_y)))
        self.assertGreaterEqual(local_edge - local_rightmost_ink, 4)


if __name__ == "__main__":
    unittest.main()
