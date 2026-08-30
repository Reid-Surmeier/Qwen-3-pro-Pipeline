from __future__ import annotations

import unittest

try:
    from PIL import Image, ImageChops

    HAVE_PIL = True
except ImportError:
    HAVE_PIL = False

if HAVE_PIL:
    from scripts import assemble_custom_filters_ro_v002 as assembly


@unittest.skipUnless(HAVE_PIL, "Pillow is not installed")
class CustomFiltersRoAssemblyV002Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = Image.open(assembly.STYLE_SOURCE).convert("RGBA")
        cls.closed, cls.permitted, cls.baseline = assembly.assemble_closed(
            cls.source
        )
        cls.open_state = assembly.assemble_open(cls.closed)

    def test_review_and_native_geometry_are_stable(self) -> None:
        self.assertEqual(self.closed.size, (1344, 504))
        self.assertEqual(self.open_state.size, (1344, 784))
        self.assertEqual(assembly.NATIVE_SIZE, (336, 126))

    def test_ok_cancel_pair_is_exact_source_pixels(self) -> None:
        source_pair = self.source.crop(assembly.SOURCE_BUTTON_PAIR_BOX)
        final_pair = self.closed.crop(assembly.TARGET_BUTTON_PAIR_BOX)
        self.assertEqual(source_pair.size, final_pair.size)
        self.assertEqual(source_pair.tobytes(), final_pair.tobytes())

    def test_dropdown_arrows_and_radios_are_exact_source_pixels(self) -> None:
        arrow = self.source.crop(assembly.SOURCE_ARROW_BOX)
        self.assertEqual(
            arrow.tobytes(),
            self.closed.crop(assembly.PAGE_ARROW_BOX).tobytes(),
        )
        self.assertEqual(
            arrow.tobytes(),
            self.closed.crop(assembly.SORT_ARROW_BOX).tobytes(),
        )
        self.assertEqual(
            self.source.crop(assembly.SOURCE_ON_RADIO_BOX).tobytes(),
            self.closed.crop(assembly.TARGET_ON_RADIO_BOX).tobytes(),
        )
        self.assertEqual(
            self.source.crop(assembly.SOURCE_OFF_RADIO_BOX).tobytes(),
            self.closed.crop(assembly.TARGET_OFF_RADIO_BOX).tobytes(),
        )

    def test_body_copy_uses_one_source_matched_size_and_row_rhythm(self) -> None:
        self.assertEqual(assembly.BODY_FONT_SIZE, 40)
        self.assertEqual({rule["size"] for rule in assembly.BODY_TEXT_RULES}, {40})
        self.assertEqual(assembly.ROW_BASELINES, (120, 204, 288))
        self.assertEqual(
            tuple(b - a for a, b in zip(assembly.ROW_BASELINES, assembly.ROW_BASELINES[1:])),
            (84, 84),
        )

    def test_required_copy_is_frozen_independently_from_production_data(self) -> None:
        expected_options = (
            "Relevance",
            "Title (a-z)",
            "Title (z-a)",
            "Date (newest-oldest)",
            "Date (oldest-newest)",
            "Artist/Maker (a-z)",
            "Artist/Maker (z-a)",
            "Accession Number (0-9)",
            "Accession Number (9-0)",
        )
        expected_copy = {
            "title": "Custom filters",
            "custom_filters": "Custom filters:",
            "images_per_page": "Images per page:",
            "page_value": "20",
            "sort_by": "Sort by:",
            "selected_sort": "Relevance",
            "choices": ("On", "Off"),
            "source_buttons": ("OK", "cancel"),
            "sort_options": expected_options,
        }
        self.assertEqual(assembly.SORT_OPTIONS, expected_options)
        self.assertEqual(assembly.EXACT_COPY, expected_copy)

    def test_source_control_sprites_are_not_rescaled(self) -> None:
        self.assertEqual(
            assembly.PAGE_FIELD_BOX[3] - assembly.PAGE_FIELD_BOX[1],
            assembly.SOURCE_DROPDOWN_BOX[3] - assembly.SOURCE_DROPDOWN_BOX[1],
        )
        self.assertEqual(
            assembly.SORT_ARROW_BOX[2] - assembly.SORT_ARROW_BOX[0],
            assembly.SOURCE_ARROW_BOX[2] - assembly.SOURCE_ARROW_BOX[0],
        )

    def test_open_popup_is_aligned_light_and_contains_all_options(self) -> None:
        self.assertEqual(assembly.POPUP_BOX[0], assembly.SORT_FIELD_BOX[0])
        self.assertEqual(assembly.POPUP_BOX[2], assembly.SORT_FIELD_BOX[2])
        popup = self.open_state.crop(assembly.POPUP_BOX)
        background = popup.getpixel((popup.width - 20, 100))
        self.assertGreater(min(background[:3]), 200)

        font = assembly.ImageFont.truetype(
            str(assembly.FONT), assembly.BODY_FONT_SIZE
        )
        widest = max(font.getbbox(option)[2] for option in assembly.SORT_OPTIONS)
        self.assertLessEqual(widest + 40, popup.width)
        last_bottom = (
            8
            + (len(assembly.SORT_OPTIONS) - 1) * assembly.POPUP_ROW_SPACING
            + max(font.getbbox(option)[3] for option in assembly.SORT_OPTIONS)
        )
        self.assertLess(last_bottom, popup.height - 4)

    def test_qwen_popup_surface_is_hash_locked_and_contains_no_donor_text(self) -> None:
        self.assertEqual(
            assembly.sha256(assembly.QWEN_POPUP_SOURCE),
            assembly.QWEN_POPUP_SOURCE_SHA256,
        )
        surface = assembly.qwen_popup_surface(
            assembly.POPUP_BOX[2] - assembly.POPUP_BOX[0],
            assembly.POPUP_BOX[3] - assembly.POPUP_BOX[1],
        )
        # Every interior scanline is extended from a donor strip that lies to
        # the right of all generated glyphs; deterministic Assembly owns text.
        for y in (20, 80, 160, 300, 460):
            left = surface.getpixel((20, y))
            right = surface.getpixel((300, y))
            self.assertLessEqual(
                max(abs(a - b) for a, b in zip(left[:3], right[:3])),
                2,
            )

    def test_actual_changes_stay_inside_predeclared_regions(self) -> None:
        actual = assembly.changed_pixel_mask(self.baseline, self.closed)
        outside = ImageChops.multiply(
            actual, ImageChops.invert(self.permitted)
        )
        self.assertIsNone(outside.getbbox())

    def test_mask_claim_is_only_relative_to_the_widened_shell(self) -> None:
        self.assertNotEqual(self.source.size, self.closed.size)
        self.assertEqual(self.baseline.size, self.closed.size)
        self.assertEqual(self.permitted.size, self.closed.size)

    def test_v001_is_retained_as_rejected_history(self) -> None:
        self.assertTrue(assembly.REJECTED_V001.exists())
        with Image.open(assembly.REJECTED_V001) as rejected:
            rejected_size = rejected.size
        self.assertNotEqual(self.closed.size, rejected_size)


if __name__ == "__main__":
    unittest.main()
