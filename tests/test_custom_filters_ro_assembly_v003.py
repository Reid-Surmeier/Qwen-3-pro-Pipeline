from __future__ import annotations

import unittest

try:
    from PIL import Image, ImageChops, ImageDraw, ImageFont

    HAVE_PIL = True
except ImportError:
    HAVE_PIL = False

if HAVE_PIL:
    from scripts import assemble_custom_filters_ro_v003 as assembly


@unittest.skipUnless(HAVE_PIL, "Pillow is not installed")
class CustomFiltersRoAssemblyV003Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = Image.open(assembly.STYLE_SOURCE).convert("RGBA")
        cls.source_native = assembly.native_source(cls.source)
        cls.shell = assembly.clean_exterior(
            assembly.extend_native_shell(cls.source_native)
        )
        cls.closed, cls.declared = assembly.assemble_closed(cls.source)
        cls.open_state = assembly.assemble_open(cls.closed)
        cls.review = assembly.closed_review(cls.closed, cls.source)
        cls.open_review = assembly.open_review(cls.open_state, cls.source)

    def test_native_and_review_geometry_is_frozen(self) -> None:
        self.assertEqual(self.source_native.size, (272, 126))
        self.assertEqual(self.closed.size, (336, 126))
        self.assertEqual(self.open_state.size, (336, 196))
        self.assertEqual(self.review.size, (1344, 504))

    def assert_review_diff_is_limited_to_source_overlays(
        self,
        native: Image.Image,
        review: Image.Image,
        overlay_boxes: tuple[tuple[int, int, int, int], ...],
    ) -> None:
        expected = assembly.review_from_native(native)
        difference = assembly.changed_pixel_mask(expected, review)
        permitted = Image.new("L", review.size, 0)
        for box in overlay_boxes:
            permitted.paste(255, box)
        outside = ImageChops.multiply(difference, ImageChops.invert(permitted))
        self.assertIsNone(outside.getbbox())

    def test_actual_closed_and_open_reviews_are_native_nearest_outside_source_overlays(self) -> None:
        shared_overlays = (
            assembly.FULL_TARGET_CLOSE_BOX,
            assembly.FULL_PAGE_ARROW_BOX,
            assembly.FULL_SORT_ARROW_BOX,
            assembly.FULL_TARGET_ON_RADIO_BOX,
            assembly.FULL_TARGET_OFF_RADIO_BOX,
        )
        self.assert_review_diff_is_limited_to_source_overlays(
            self.closed,
            self.review,
            shared_overlays + (assembly.FULL_TARGET_BUTTON_PAIR_BOX,),
        )
        self.assert_review_diff_is_limited_to_source_overlays(
            self.open_state,
            self.open_review,
            shared_overlays,
        )

    def test_review_controls_are_byte_exact_full_resolution_source_pixels(self) -> None:
        pairs = (
            (assembly.FULL_SOURCE_CLOSE_BOX, assembly.FULL_TARGET_CLOSE_BOX),
            (assembly.FULL_SOURCE_ARROW_BOX, assembly.FULL_PAGE_ARROW_BOX),
            (assembly.FULL_SOURCE_ARROW_BOX, assembly.FULL_SORT_ARROW_BOX),
            (assembly.FULL_SOURCE_ON_RADIO_BOX, assembly.FULL_TARGET_ON_RADIO_BOX),
            (assembly.FULL_SOURCE_OFF_RADIO_BOX, assembly.FULL_TARGET_OFF_RADIO_BOX),
            (assembly.FULL_SOURCE_BUTTON_PAIR_BOX, assembly.FULL_TARGET_BUTTON_PAIR_BOX),
        )
        for source_box, target_box in pairs:
            with self.subTest(source_box=source_box, target_box=target_box):
                self.assertEqual(
                    self.source.crop(source_box).tobytes(),
                    self.review.crop(target_box).tobytes(),
                )

    def test_exterior_caps_and_named_controls_are_exact_native_source_pixels(self) -> None:
        exact_pairs = (
            (assembly.SOURCE_LEFT_CAP_BOX, assembly.TARGET_LEFT_CAP_BOX),
            (assembly.SOURCE_RIGHT_CAP_BOX, assembly.TARGET_RIGHT_CAP_BOX),
            (assembly.SOURCE_CLOSE_BOX, assembly.TARGET_CLOSE_BOX),
            (assembly.SOURCE_ARROW_BOX, assembly.PAGE_ARROW_BOX),
            (assembly.SOURCE_ARROW_BOX, assembly.SORT_ARROW_BOX),
            (assembly.SOURCE_ON_RADIO_BOX, assembly.TARGET_ON_RADIO_BOX),
            (assembly.SOURCE_OFF_RADIO_BOX, assembly.TARGET_OFF_RADIO_BOX),
            (assembly.SOURCE_BUTTON_PAIR_BOX, assembly.TARGET_BUTTON_PAIR_BOX),
        )
        for source_box, target_box in exact_pairs:
            with self.subTest(source_box=source_box, target_box=target_box):
                self.assertEqual(
                    self.source_native.crop(source_box).tobytes(),
                    self.closed.crop(target_box).tobytes(),
                )

    def test_noisy_screenshot_exterior_is_replaced_by_clean_native_edges(self) -> None:
        self.assertEqual(self.closed.getpixel((0, 0)), assembly.WHITE)
        self.assertEqual(self.closed.getpixel((335, 0)), assembly.WHITE)
        self.assertNotEqual(
            self.source_native.getpixel((0, 0)),
            self.closed.getpixel((0, 0)),
        )

    def test_all_body_and_popup_copy_uses_native_ten_pixel_font(self) -> None:
        self.assertEqual(assembly.BODY_FONT_SIZE, 10)
        self.assertEqual({rule["size"] for rule in assembly.BODY_TEXT_RULES}, {10})
        self.assertEqual(assembly.POPUP_FONT_SIZE, 10)
        self.assertEqual(assembly.ROW_BASELINES, (30, 51, 72))
        self.assertEqual(
            tuple(b - a for a, b in zip(assembly.ROW_BASELINES, assembly.ROW_BASELINES[1:])),
            (21, 21),
        )

    def test_popup_aligns_to_sort_field_and_every_option_is_contained(self) -> None:
        self.assertEqual(assembly.POPUP_BOX[0], assembly.SORT_FIELD_BOX[0])
        self.assertEqual(assembly.POPUP_BOX[2], assembly.SORT_FIELD_BOX[2])
        self.assertEqual(assembly.POPUP_BOX[1], assembly.SORT_FIELD_BOX[3] - 1)
        popup_width = assembly.POPUP_BOX[2] - assembly.POPUP_BOX[0]
        popup_height = assembly.POPUP_BOX[3] - assembly.POPUP_BOX[1]
        font = ImageFont.truetype(str(assembly.FONT), assembly.POPUP_FONT_SIZE)
        draw = ImageDraw.Draw(Image.new("RGBA", (popup_width, popup_height)))
        for index, option in enumerate(assembly.SORT_OPTIONS):
            xy = (5, 2 + index * assembly.POPUP_ROW_SPACING)
            bounds = draw.textbbox(xy, option, font=font)
            with self.subTest(option=option):
                self.assertGreaterEqual(bounds[0], 1)
                self.assertGreaterEqual(bounds[1], 1)
                self.assertLessEqual(bounds[2], popup_width - 1)
                self.assertLessEqual(bounds[3], popup_height - 1)

    def test_required_copy_is_independently_frozen(self) -> None:
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
        self.assertEqual(assembly.SORT_OPTIONS, expected_options)
        self.assertEqual(
            assembly.EXACT_COPY,
            {
                "title": "Custom filters",
                "custom_filters": "Custom filters:",
                "images_per_page": "Images per page:",
                "page_value": "20",
                "sort_by": "Sort by:",
                "selected_sort": "Relevance",
                "choices": ("On", "Off"),
                "source_buttons": ("OK", "cancel"),
                "sort_options": expected_options,
            },
        )

    def test_changes_are_contained_relative_to_predeclared_native_shell_mask(self) -> None:
        actual = assembly.changed_pixel_mask(self.shell, self.closed)
        outside = ImageChops.multiply(actual, ImageChops.invert(self.declared))
        self.assertIsNone(outside.getbbox())

    def test_v001_and_v002_are_retained_as_rejected_history(self) -> None:
        self.assertTrue(assembly.REJECTED_V001.exists())
        self.assertTrue(assembly.REJECTED_V002.exists())


if __name__ == "__main__":
    unittest.main()
