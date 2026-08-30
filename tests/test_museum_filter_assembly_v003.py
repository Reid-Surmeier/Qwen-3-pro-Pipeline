from __future__ import annotations

import unittest
from pathlib import Path

from PIL import Image, ImageChops

from scripts import assemble_museum_filter_v003 as assembly


ROOT = Path(__file__).resolve().parents[1]


class ShapeAwareMuseumFilterAssemblyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.baseline = Image.open(
            ROOT
            / "artifacts/runs/museum-filter-assembly-v001/assembly-v001-native.png"
        ).convert("RGB")
        cls.donor = Image.open(
            ROOT / "artifacts/runs/museum-filter-retro-skin-v005/image-02.png"
        ).convert("RGB")
        cls.output, cls.mask = assembly.assemble_native(cls.baseline, cls.donor)

    def test_mask_is_the_actual_changed_pixel_shape(self) -> None:
        actual = assembly.changed_pixel_mask(self.baseline, self.output)
        self.assertEqual(self.mask.tobytes(), actual.tobytes())

        changed = sum(1 for value in self.mask.getdata() if value)
        self.assertGreater(changed, 500)
        self.assertLess(changed, 8_000)

    def test_v001_header_chrome_and_right_controls_are_immutable(self) -> None:
        # Only the title glyph silhouette may change in the header. The blue
        # glass, right bead and close button remain byte-identical to v001.
        protected = (160, 3, 310, 23)
        self.assertEqual(
            self.baseline.crop(protected).tobytes(),
            self.output.crop(protected).tobytes(),
        )

        title_box = (20, 6, 160, 21)
        header_diff = ImageChops.difference(
            self.baseline.crop((3, 3, 310, 23)),
            self.output.crop((3, 3, 310, 23)),
        )
        allowed = Image.new("L", header_diff.size, 0)
        local_title = (
            title_box[0] - 3,
            title_box[1] - 3,
            title_box[2] - 3,
            title_box[3] - 3,
        )
        allowed.paste(255, local_title)
        outside = ImageChops.multiply(
            header_diff.convert("L"), ImageChops.invert(allowed)
        )
        self.assertIsNone(outside.getbbox())

    def test_no_text_or_tab_edit_owns_its_enclosing_rectangle(self) -> None:
        for box in assembly.EDIT_BOXES:
            region = self.mask.crop(box)
            changed = sum(1 for value in region.getdata() if value)
            area = region.width * region.height
            self.assertGreater(changed, 0, box)
            self.assertLess(changed / area, 0.72, box)

    def test_all_changes_stay_inside_declared_glyph_and_tab_boxes(self) -> None:
        allowed = Image.new("L", self.baseline.size, 0)
        for box in assembly.EDIT_BOXES:
            allowed.paste(255, box)
        outside = ImageChops.multiply(self.mask, ImageChops.invert(allowed))
        self.assertIsNone(outside.getbbox())


if __name__ == "__main__":
    unittest.main()
