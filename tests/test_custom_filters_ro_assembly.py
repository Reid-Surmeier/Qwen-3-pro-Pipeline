from __future__ import annotations

import unittest
from pathlib import Path

try:
    from PIL import Image, ImageChops

    HAVE_PIL = True
except ImportError:
    HAVE_PIL = False

if HAVE_PIL:
    from scripts import assemble_custom_filters_ro as assembly


ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(HAVE_PIL, "Pillow is not installed")
class CustomFiltersRoAssemblyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = Image.open(assembly.STYLE_SOURCE).convert("RGBA")
        cls.baseline = assembly.native_source(cls.source)
        cls.closed, cls.declared = assembly.assemble_closed(cls.source)
        cls.actual = assembly.changed_pixel_mask(cls.baseline, cls.closed)
        cls.open_state = assembly.assemble_open(cls.closed)

    def test_native_and_open_state_dimensions_are_stable(self) -> None:
        self.assertEqual(self.baseline.size, (272, 126))
        self.assertEqual(self.closed.size, (272, 126))
        self.assertEqual(self.open_state.size, (272, 196))

    def test_actual_difference_is_inside_predeclared_edit_regions(self) -> None:
        allowed = Image.new("L", self.baseline.size, 0)
        for box in assembly.EDIT_BOXES:
            allowed.paste(255, box)
        self.assertEqual(self.declared.tobytes(), allowed.tobytes())
        outside = ImageChops.multiply(self.actual, ImageChops.invert(self.declared))
        self.assertIsNone(outside.getbbox())

    def test_outer_frame_and_shadow_are_source_pixels(self) -> None:
        frozen = Image.new("L", self.baseline.size, 255)
        for box in assembly.EDIT_BOXES:
            frozen.paste(0, box)
        difference = assembly.changed_pixel_mask(self.baseline, self.closed)
        self.assertIsNone(ImageChops.multiply(difference, frozen).getbbox())

    def test_exact_copy_and_sort_order_are_frozen(self) -> None:
        self.assertEqual(assembly.EXACT_COPY["title"], "Custom filters")
        self.assertEqual(assembly.EXACT_COPY["images_per_page"], "Images per page:")
        self.assertEqual(assembly.EXACT_COPY["selected_sort"], "Relevance")
        self.assertEqual(assembly.EXACT_COPY["choices"], ("On", "Off"))
        self.assertEqual(
            assembly.SORT_OPTIONS,
            (
                "Relevance",
                "Title (a-z)",
                "Title (z-a)",
                "Date (newest-oldest)",
                "Date (oldest-newest)",
                "Artist/Maker (a-z)",
                "Artist/Maker (z-a)",
                "Accession Number (0-9)",
                "Accession Number (9-0)",
            ),
        )

    def test_body_font_provenance_is_pinned(self) -> None:
        self.assertEqual(
            assembly.FONT_SHA256,
            "01b5e4aea5a3bbe80463c178e7868d5a34cd75e8ed7bc4d97097ebb1a71af7c7",
        )
        self.assertEqual(assembly.sha256(assembly.FONT), assembly.FONT_SHA256)

    def test_source_dropdown_and_radio_chrome_are_reused(self) -> None:
        arrow = self.baseline.crop(assembly.SOURCE_ARROW_BOX)
        self.assertEqual(
            arrow.tobytes(),
            self.closed.crop(assembly.PAGE_ARROW_BOX).tobytes(),
        )
        self.assertEqual(
            arrow.tobytes(),
            self.closed.crop(assembly.SORT_ARROW_BOX).tobytes(),
        )
        self.assertEqual(
            self.baseline.crop(assembly.SOURCE_ON_RADIO_BOX).tobytes(),
            self.closed.crop(assembly.ON_RADIO_BOX).tobytes(),
        )
        self.assertEqual(
            self.baseline.crop(assembly.SOURCE_OFF_RADIO_BOX).tobytes(),
            self.closed.crop(assembly.OFF_RADIO_BOX).tobytes(),
        )

    def test_password_field_is_removed_and_open_menu_is_not_clipped(self) -> None:
        self.assertNotEqual(
            self.baseline.crop(assembly.SOURCE_PASSWORD_BOX).tobytes(),
            self.closed.crop(assembly.SOURCE_PASSWORD_BOX).tobytes(),
        )
        popup = assembly.POPUP_BOX
        self.assertLessEqual(popup[2], self.open_state.width)
        self.assertLessEqual(popup[3], self.open_state.height)
        self.assertGreater(popup[3], self.closed.height)


if __name__ == "__main__":
    unittest.main()
