#!/usr/bin/env python3.12
"""Build Issue #138 v005 entirely on the source's native pixel grid.

The shell is widened at 272x126 native resolution by inserting a bounded
center strip. The exterior caps and all named controls remain exact native
source pixels. Text is drawn once at 10px and every 4x review export is a
nearest-neighbor enlargement. Body and title glyphs use one restrained,
source-directed native edge layer instead of stacked duplicate glyphs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "artifacts/references/custom-filters-ro-v001"
STYLE_SOURCE = REFERENCE_DIR / "style-chat-room.png"
DATA_SOURCE = REFERENCE_DIR / "data-sort-dropdown.png"
RENDER_RUN = ROOT / "artifacts/runs/custom-filters-ro-render-v001"
QWEN_POPUP_SOURCE = RENDER_RUN / "image-01.png"
QWEN_POPUP_SOURCE_SHA256 = "b61a9c82e151ab3e1db5e4557644f27ba4c9da3030c98038c1a0f41ab92e355c"
QWEN_POPUP_BOX = (1150, 374, 1768, 864)
QWEN_SELECTED_ROW_BOTTOM = 64
REJECTED_V001 = ROOT / "artifacts/runs/custom-filters-ro-assembly-v001/custom-filters-closed.png"
REJECTED_V002 = ROOT / "artifacts/runs/custom-filters-ro-assembly-v002/custom-filters-closed.png"
REJECTED_V003 = ROOT / "artifacts/runs/custom-filters-ro-assembly-v003/custom-filters-closed.png"
REJECTED_V004 = ROOT / "artifacts/runs/custom-filters-ro-assembly-v004/custom-filters-closed.png"
TITLE_TEXT_AUTHORITY = REFERENCE_DIR / "title-text-authority.png"
TITLE_TEXT_AUTHORITY_SHA256 = "0e297d8786a0d8413b31c776f0beecd0fb6422e08eeb9e8f4de46d5997cd2caa"
DEFAULT_OUTPUT = ROOT / "artifacts/runs/custom-filters-ro-assembly-v005"
FONT = ROOT / "godot/fonts/PixelMplus10-Regular.ttf"
FONT_SHA256 = "01b5e4aea5a3bbe80463c178e7868d5a34cd75e8ed7bc4d97097ebb1a71af7c7"
TITLE_FONT = ROOT / "godot/fonts/PixelMplus12-Regular.ttf"
TITLE_FONT_SHA256 = "02f19467ea7cc235cc06c570b7f6c3b0a12a6f682bc8d74c43f2d323d97bcd12"

SOURCE_FULL_SIZE = (1088, 504)
SOURCE_NATIVE_SIZE = (272, 126)
NATIVE_SIZE = (336, 126)
OPEN_NATIVE_SIZE = (336, 196)
SCALE = 4
REVIEW_SIZE = (1344, 504)
OPEN_REVIEW_SIZE = (1344, 784)
INSERT_AT = 136
INSERT_WIDTH = 64

BODY_FONT_SIZE = 10
POPUP_FONT_SIZE = 10
TITLE_FONT_SIZE = 12
ROW_BASELINES = (30, 51, 72)
POPUP_ROW_SPACING = 14

SOURCE_LEFT_CAP_BOX = (8, 10, 12, 115)
TARGET_LEFT_CAP_BOX = SOURCE_LEFT_CAP_BOX
SOURCE_RIGHT_CAP_BOX = (260, 10, 264, 115)
TARGET_RIGHT_CAP_BOX = (324, 10, 328, 115)
SOURCE_CLOSE_BOX = (248, 9, 259, 22)
TARGET_CLOSE_BOX = (312, 9, 323, 22)
SOURCE_ARROW_BOX = (117, 50, 133, 65)
PAGE_ARROW_BOX = (138, 50, 154, 65)
SORT_ARROW_BOX = (308, 50, 324, 65)
SOURCE_ON_RADIO_BOX = (49, 70, 61, 84)
SOURCE_OFF_RADIO_BOX = (85, 70, 97, 84)
TARGET_ON_RADIO_BOX = SOURCE_ON_RADIO_BOX
TARGET_OFF_RADIO_BOX = SOURCE_OFF_RADIO_BOX
SOURCE_BUTTON_PAIR_BOX = (178, 94, 259, 115)
TARGET_BUTTON_PAIR_BOX = (242, 94, 323, 115)

FULL_SOURCE_CLOSE_BOX = (992, 36, 1036, 88)
FULL_TARGET_CLOSE_BOX = (1248, 36, 1292, 88)
FULL_SOURCE_ARROW_BOX = (468, 200, 532, 260)
FULL_PAGE_ARROW_BOX = (552, 200, 616, 260)
FULL_SORT_ARROW_BOX = (1232, 200, 1296, 260)
FULL_SOURCE_ON_RADIO_BOX = (196, 280, 244, 336)
FULL_SOURCE_OFF_RADIO_BOX = (340, 280, 388, 336)
FULL_TARGET_ON_RADIO_BOX = FULL_SOURCE_ON_RADIO_BOX
FULL_TARGET_OFF_RADIO_BOX = FULL_SOURCE_OFF_RADIO_BOX
FULL_SOURCE_BUTTON_PAIR_BOX = (712, 376, 1036, 460)
FULL_TARGET_BUTTON_PAIR_BOX = (968, 376, 1292, 460)

TITLE_EDIT_BOX = (12, 6, 324, 24)
BODY_EDIT_BOX = (12, 24, 324, 90)
EDIT_BOXES = (TITLE_EDIT_BOX, BODY_EDIT_BOX)

TITLE_FIELD_BOX = (94, 28, 324, 45)
PAGE_FIELD_BOX = (98, 49, 154, 65)
SORT_FIELD_BOX = (204, 49, 324, 65)
POPUP_BOX = (204, 64, 324, 192)

LABEL_INK = (46, 69, 96, 255)
BODY_DEPTH_INK = (188, 197, 206, 255)
TITLE_INK = (0, 1, 7, 255)
TITLE_EDGE_INK = (250, 255, 255, 255)
WHITE = (255, 255, 255, 255)

LABEL_TEXT_EFFECTS = (
    ((1, 1), BODY_DEPTH_INK),
    ((0, 0), LABEL_INK),
)
VALUE_TEXT_EFFECTS = (
    ((1, 1), BODY_DEPTH_INK),
    ((0, 0), LABEL_INK),
)
TITLE_TEXT_EFFECTS = (
    ((1, 1), TITLE_EDGE_INK),
    ((0, 0), TITLE_INK),
)

SORT_OPTIONS = (
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

EXACT_COPY = {
    "title": "Custom filters",
    "custom_filters": "Custom filters:",
    "images_per_page": "Images per page:",
    "page_value": "20",
    "sort_by": "Sort by:",
    "selected_sort": "Relevance",
    "choices": ("On", "Off"),
    "source_buttons": ("OK", "cancel"),
    "sort_options": SORT_OPTIONS,
}

BODY_TEXT_RULES = (
    {"text": EXACT_COPY["custom_filters"], "xy": (14, ROW_BASELINES[0]), "size": BODY_FONT_SIZE, "effects": LABEL_TEXT_EFFECTS},
    {"text": EXACT_COPY["images_per_page"], "xy": (13, ROW_BASELINES[1]), "size": BODY_FONT_SIZE, "effects": LABEL_TEXT_EFFECTS},
    {"text": EXACT_COPY["page_value"], "xy": (102, ROW_BASELINES[1]), "size": BODY_FONT_SIZE, "effects": VALUE_TEXT_EFFECTS},
    {"text": EXACT_COPY["sort_by"], "xy": (160, ROW_BASELINES[1]), "size": BODY_FONT_SIZE, "effects": LABEL_TEXT_EFFECTS},
    {"text": EXACT_COPY["selected_sort"], "xy": (208, ROW_BASELINES[1]), "size": BODY_FONT_SIZE, "effects": VALUE_TEXT_EFFECTS},
    {"text": EXACT_COPY["choices"][0], "xy": (63, ROW_BASELINES[2]), "size": BODY_FONT_SIZE, "effects": VALUE_TEXT_EFFECTS},
    {"text": EXACT_COPY["choices"][1], "xy": (100, ROW_BASELINES[2]), "size": BODY_FONT_SIZE, "effects": VALUE_TEXT_EFFECTS},
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def repo_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def native_source(source: Image.Image) -> Image.Image:
    source = source.convert("RGBA")
    if source.size != SOURCE_FULL_SIZE:
        raise ValueError(f"style source must be {SOURCE_FULL_SIZE}, got {source.size}")
    return source.resize(SOURCE_NATIVE_SIZE, Image.Resampling.NEAREST)


def extend_native_shell(source: Image.Image) -> Image.Image:
    if source.size != SOURCE_NATIVE_SIZE:
        raise ValueError(f"native source must be {SOURCE_NATIVE_SIZE}, got {source.size}")
    output = Image.new("RGBA", NATIVE_SIZE)
    output.paste(source.crop((0, 0, INSERT_AT, source.height)), (0, 0))
    bridge = source.crop((INSERT_AT - 4, 0, INSERT_AT + 4, source.height)).resize(
        (INSERT_WIDTH, source.height), Image.Resampling.NEAREST
    )
    output.paste(bridge, (INSERT_AT, 0))
    output.paste(
        source.crop((INSERT_AT, 0, source.width, source.height)),
        (INSERT_AT + INSERT_WIDTH, 0),
    )
    return output


def clean_exterior(shell: Image.Image) -> Image.Image:
    """Remove screenshot-edge stipple while retaining the inner RO frame."""
    output = Image.new("RGBA", NATIVE_SIZE, WHITE)
    draw = ImageDraw.Draw(output)
    draw.rounded_rectangle(
        (1, 0, NATIVE_SIZE[0] - 2, NATIVE_SIZE[1] - 2),
        radius=8,
        fill=WHITE,
        outline=(196, 196, 196, 255),
        width=1,
    )
    interior_mask = Image.new("L", NATIVE_SIZE, 0)
    ImageDraw.Draw(interior_mask).rounded_rectangle(
        (7, 5, NATIVE_SIZE[0] - 8, NATIVE_SIZE[1] - 7),
        radius=5,
        fill=255,
    )
    output.paste(shell, (0, 0), interior_mask)
    return output


def changed_pixel_mask(before: Image.Image, after: Image.Image) -> Image.Image:
    difference = ImageChops.difference(before.convert("RGBA"), after.convert("RGBA"))
    channels = difference.split()
    maximum = channels[0]
    for channel in channels[1:]:
        maximum = ImageChops.lighter(maximum, channel)
    return maximum.point(lambda value: 255 if value else 0)


def native_edit_mask() -> Image.Image:
    mask = Image.new("L", NATIVE_SIZE, 0)
    for box in EDIT_BOXES:
        mask.paste(255, box)
    return mask


def count_pixels(mask: Image.Image) -> int:
    return sum(mask.convert("L").histogram()[1:])


def draw_text(
    image: Image.Image,
    xy: tuple[int, int],
    text: str,
    *,
    size: int,
    effects: tuple[
        tuple[tuple[int, int], tuple[int, int, int, int]], ...
    ],
    font_path: Path = FONT,
) -> None:
    draw = ImageDraw.Draw(image)
    draw.fontmode = "1"
    font = ImageFont.truetype(str(font_path), size)
    for (offset_x, offset_y), fill in effects:
        draw.text(
            (xy[0] + offset_x, xy[1] + offset_y),
            text,
            font=font,
            fill=fill,
        )


def native_nine_slice(source: Image.Image, width: int, cap: int = 3) -> Image.Image:
    if width < cap * 2:
        raise ValueError("target is narrower than source caps")
    output = Image.new(source.mode, (width, source.height))
    output.paste(source.crop((0, 0, cap, source.height)), (0, 0))
    middle = source.crop((cap, 0, source.width - cap, source.height)).resize(
        (width - cap * 2, source.height), Image.Resampling.NEAREST
    )
    output.paste(middle, (cap, 0))
    output.paste(
        source.crop((source.width - cap, 0, source.width, source.height)),
        (width - cap, 0),
    )
    return output


def clean_dropdown(source: Image.Image, width: int) -> Image.Image:
    control = source.crop((49, 49, 133, 65))
    blank = source.crop((52, 31, 114, 43))
    control.paste(blank, (3, 3))
    arrow_width = SOURCE_ARROW_BOX[2] - SOURCE_ARROW_BOX[0]
    body = control.crop((0, 0, control.width - arrow_width, control.height))
    output = Image.new("RGBA", (width, control.height))
    output.paste(native_nine_slice(body, width - arrow_width), (0, 0))
    output.paste(control.crop((control.width - arrow_width, 0, control.width, control.height)), (width - arrow_width, 0))
    return output


def clean_title_surface(source: Image.Image) -> Image.Image:
    donor = source.crop((108, 7, 244, 23))
    return donor.resize(
        (TITLE_EDIT_BOX[2] - TITLE_EDIT_BOX[0], TITLE_EDIT_BOX[3] - TITLE_EDIT_BOX[1]),
        Image.Resampling.BILINEAR,
    )


def clean_body_surface(source: Image.Image) -> Image.Image:
    # Native x=257 is the clean white body column immediately before the
    # magenta edge; stretching it preserves the source's vertical tone profile.
    donor = source.crop((257, BODY_EDIT_BOX[1], 258, BODY_EDIT_BOX[3]))
    return donor.resize(
        (BODY_EDIT_BOX[2] - BODY_EDIT_BOX[0], BODY_EDIT_BOX[3] - BODY_EDIT_BOX[1]),
        Image.Resampling.NEAREST,
    )


def assemble_closed(source: Image.Image) -> tuple[Image.Image, Image.Image]:
    native = native_source(source)
    shell = clean_exterior(extend_native_shell(native))
    declared = native_edit_mask()
    output = shell.copy()

    output.paste(clean_title_surface(native), TITLE_EDIT_BOX[:2])
    output.paste(native.crop(SOURCE_CLOSE_BOX), TARGET_CLOSE_BOX[:2])
    draw_text(
        output,
        (15, 9),
        EXACT_COPY["title"],
        size=TITLE_FONT_SIZE,
        effects=TITLE_TEXT_EFFECTS,
        font_path=TITLE_FONT,
    )

    output.paste(clean_body_surface(native), BODY_EDIT_BOX[:2])

    blank_field = native.crop((49, 28, 256, 45))
    output.paste(native_nine_slice(blank_field, TITLE_FIELD_BOX[2] - TITLE_FIELD_BOX[0]), TITLE_FIELD_BOX[:2])
    output.paste(clean_dropdown(native, PAGE_FIELD_BOX[2] - PAGE_FIELD_BOX[0]), PAGE_FIELD_BOX[:2])
    output.paste(clean_dropdown(native, SORT_FIELD_BOX[2] - SORT_FIELD_BOX[0]), SORT_FIELD_BOX[:2])

    output.paste(native.crop(SOURCE_ON_RADIO_BOX), TARGET_ON_RADIO_BOX[:2])
    output.paste(native.crop(SOURCE_OFF_RADIO_BOX), TARGET_OFF_RADIO_BOX[:2])

    for rule in BODY_TEXT_RULES:
        draw_text(
            output,
            rule["xy"],
            rule["text"],
            size=rule["size"],
            effects=rule["effects"],
        )

    actual = changed_pixel_mask(shell, output)
    outside = ImageChops.multiply(actual, ImageChops.invert(declared))
    if outside.getbbox() is not None:
        raise RuntimeError(f"native Assembly changed pixels outside its mask: {outside.getbbox()}")
    return output, declared


def qwen_popup_surface(width: int, height: int) -> Image.Image:
    if sha256(QWEN_POPUP_SOURCE) != QWEN_POPUP_SOURCE_SHA256:
        raise RuntimeError("Qwen popup donor hash does not match")
    with Image.open(QWEN_POPUP_SOURCE) as generated:
        donor = generated.convert("RGBA").crop(QWEN_POPUP_BOX)
    donor = donor.resize((width, height), Image.Resampling.BILINEAR)
    strip = donor.crop((width - 13, 1, width - 5, height - 1))
    source_height = QWEN_POPUP_BOX[3] - QWEN_POPUP_BOX[1]
    selected_bottom = round(QWEN_SELECTED_ROW_BOTTOM * height / source_height)
    panel = Image.new("RGBA", (width, height))
    panel.paste(strip.crop((0, 0, strip.width, selected_bottom - 1)).resize((width - 2, 13), Image.Resampling.BILINEAR), (1, 1))
    panel.paste(strip.crop((0, selected_bottom - 1, strip.width, strip.height)).resize((width - 2, height - 15), Image.Resampling.BILINEAR), (1, 14))
    panel.paste(donor.crop((0, 0, width, 1)), (0, 0))
    panel.paste(donor.crop((0, height - 1, width, height)), (0, height - 1))
    panel.paste(donor.crop((0, 0, 1, height)), (0, 0))
    panel.paste(donor.crop((width - 1, 0, width, height)), (width - 1, 0))
    return panel


def open_baseline(closed: Image.Image) -> Image.Image:
    if closed.size != NATIVE_SIZE:
        raise ValueError(f"closed state must be {NATIVE_SIZE}, got {closed.size}")
    output = Image.new("RGBA", OPEN_NATIVE_SIZE, (0, 0, 0, 0))
    output.paste(closed, (0, 0))
    return output


def open_edit_mask() -> Image.Image:
    mask = Image.new("L", OPEN_NATIVE_SIZE, 0)
    mask.paste(255, POPUP_BOX)
    return mask


def assemble_open(closed: Image.Image) -> Image.Image:
    output = open_baseline(closed)
    width = POPUP_BOX[2] - POPUP_BOX[0]
    height = POPUP_BOX[3] - POPUP_BOX[1]
    panel = qwen_popup_surface(width, height)
    for index, option in enumerate(SORT_OPTIONS):
        draw_text(
            panel,
            (5, 2 + index * POPUP_ROW_SPACING),
            option,
            size=POPUP_FONT_SIZE,
            effects=VALUE_TEXT_EFFECTS,
        )
    output.paste(panel, POPUP_BOX[:2])
    return output


def review_from_native(image: Image.Image) -> Image.Image:
    return image.resize((image.width * SCALE, image.height * SCALE), Image.Resampling.NEAREST)


def overlay_full_source_controls(
    review: Image.Image,
    source: Image.Image,
    *,
    include_buttons: bool = True,
) -> Image.Image:
    output = review.copy()
    pairs = (
        (FULL_SOURCE_CLOSE_BOX, FULL_TARGET_CLOSE_BOX),
        (FULL_SOURCE_ARROW_BOX, FULL_PAGE_ARROW_BOX),
        (FULL_SOURCE_ARROW_BOX, FULL_SORT_ARROW_BOX),
        (FULL_SOURCE_ON_RADIO_BOX, FULL_TARGET_ON_RADIO_BOX),
        (FULL_SOURCE_OFF_RADIO_BOX, FULL_TARGET_OFF_RADIO_BOX),
    )
    for source_box, target_box in pairs:
        output.paste(source.crop(source_box), target_box[:2])
    if include_buttons:
        output.paste(
            source.crop(FULL_SOURCE_BUTTON_PAIR_BOX),
            FULL_TARGET_BUTTON_PAIR_BOX[:2],
        )
    return output


def closed_review(closed: Image.Image, source: Image.Image) -> Image.Image:
    return overlay_full_source_controls(review_from_native(closed), source)


def open_review(open_state: Image.Image, source: Image.Image) -> Image.Image:
    # The open popup visually covers the footer button pair, so do not paste
    # that closed-state source crop over it.
    return overlay_full_source_controls(
        review_from_native(open_state), source, include_buttons=False
    )


def make_contact_sheet(source: Image.Image, rejected: Image.Image, closed: Image.Image, open_state: Image.Image) -> Image.Image:
    closed_review_image = closed_review(closed, source).convert("RGB")
    open_review_image = open_review(open_state, source).convert("RGBA")
    open_back = Image.new("RGB", open_review_image.size, WHITE[:3])
    open_back.paste(open_review_image, (0, 0), open_review_image.getchannel("A"))
    source = source.convert("RGB")
    rejected = rejected.convert("RGB")
    margin = 20
    width = max(source.width + rejected.width + 3 * margin, closed_review_image.width + 2 * margin, open_back.width + 2 * margin)
    height = 28 + max(source.height, rejected.height) + 36 + closed_review_image.height + 36 + open_back.height + margin
    sheet = Image.new("RGB", (width, height), (32, 35, 43))
    draw = ImageDraw.Draw(sheet)
    draw.text((margin, 7), "style source / rejected v004", fill=(255, 255, 255))
    y = 28
    sheet.paste(source, (margin, y))
    sheet.paste(rejected, (source.width + 2 * margin, y))
    y += max(source.height, rejected.height)
    draw.text((margin, y + 9), "v005 closed - restrained one-pixel text depth", fill=(255, 255, 255))
    y += 36
    sheet.paste(closed_review_image, (margin, y))
    y += closed_review_image.height
    draw.text((margin, y + 9), "v005 open - restrained deterministic text over masked Qwen surface", fill=(255, 255, 255))
    y += 36
    sheet.paste(open_back, (margin, y))
    return sheet


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--style-source", type=Path, default=STYLE_SOURCE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    style_path = args.style_source.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    if sha256(FONT) != FONT_SHA256:
        raise RuntimeError("pinned PixelMplus font hash does not match")
    if sha256(TITLE_FONT) != TITLE_FONT_SHA256:
        raise RuntimeError("pinned PixelMplus title font hash does not match")

    with Image.open(style_path) as image:
        source = image.convert("RGBA")
    native = native_source(source)
    shell = clean_exterior(extend_native_shell(native))
    closed, declared = assemble_closed(source)
    open_state = assemble_open(closed)
    open_base = open_baseline(closed)
    open_declared = open_edit_mask()
    open_actual = changed_pixel_mask(open_base, open_state)
    open_outside = ImageChops.multiply(
        open_actual, ImageChops.invert(open_declared)
    )
    if open_outside.getbbox() is not None:
        raise RuntimeError(
            f"open Assembly changed pixels outside its mask: {open_outside.getbbox()}"
        )
    actual = changed_pixel_mask(shell, closed)
    outside = ImageChops.multiply(actual, ImageChops.invert(declared))

    paths = {
        "closed_native": output_dir / "custom-filters-closed-native.png",
        "closed": output_dir / "custom-filters-closed.png",
        "open_native": output_dir / "custom-filters-open-native.png",
        "open": output_dir / "custom-filters-open.png",
        "declared_native": output_dir / "native-edit-mask.png",
        "declared": output_dir / "native-edit-mask-4x.png",
        "actual_native": output_dir / "actual-difference-mask-native.png",
        "actual": output_dir / "actual-difference-mask-4x.png",
        "open_declared_native": output_dir / "open-native-edit-mask.png",
        "open_declared": output_dir / "open-native-edit-mask-4x.png",
        "open_actual_native": output_dir / "open-actual-difference-mask-native.png",
        "open_actual": output_dir / "open-actual-difference-mask-4x.png",
        "contact": output_dir / "contact-sheet.png",
    }
    closed.save(paths["closed_native"])
    closed_review(closed, source).save(paths["closed"])
    open_state.save(paths["open_native"])
    open_review(open_state, source).save(paths["open"])
    declared.save(paths["declared_native"])
    review_from_native(declared).save(paths["declared"])
    actual.save(paths["actual_native"])
    review_from_native(actual).save(paths["actual"])
    open_declared.save(paths["open_declared_native"])
    review_from_native(open_declared).save(paths["open_declared"])
    open_actual.save(paths["open_actual_native"])
    review_from_native(open_actual).save(paths["open_actual"])
    with Image.open(REJECTED_V004) as rejected:
        make_contact_sheet(source, rejected, closed, open_state).save(paths["contact"])

    exact_pairs = {
        "left_exterior_cap": (SOURCE_LEFT_CAP_BOX, TARGET_LEFT_CAP_BOX),
        "right_exterior_cap": (SOURCE_RIGHT_CAP_BOX, TARGET_RIGHT_CAP_BOX),
        "close": (SOURCE_CLOSE_BOX, TARGET_CLOSE_BOX),
        "page_arrow": (SOURCE_ARROW_BOX, PAGE_ARROW_BOX),
        "sort_arrow": (SOURCE_ARROW_BOX, SORT_ARROW_BOX),
        "on_radio": (SOURCE_ON_RADIO_BOX, TARGET_ON_RADIO_BOX),
        "off_radio": (SOURCE_OFF_RADIO_BOX, TARGET_OFF_RADIO_BOX),
        "button_pair": (SOURCE_BUTTON_PAIR_BOX, TARGET_BUTTON_PAIR_BOX),
    }
    exact_results = {
        name: native.crop(source_box).tobytes() == closed.crop(target_box).tobytes()
        for name, (source_box, target_box) in exact_pairs.items()
    }
    verification = {
        "issue": 138,
        "assembly": "custom-filters-ro-v005",
        "status": "candidate_pending_owner_visual_approval",
        "style_source": repo_path(style_path),
        "style_source_sha256": sha256(style_path),
        "data_source": repo_path(DATA_SOURCE),
        "data_source_sha256": sha256(DATA_SOURCE),
        "data_source_usage": "strings and order only",
        "rejected_parents": [repo_path(REJECTED_V001), repo_path(REJECTED_V002), repo_path(REJECTED_V003), repo_path(REJECTED_V004)],
        "title_text_authority": repo_path(TITLE_TEXT_AUTHORITY),
        "title_text_authority_sha256": TITLE_TEXT_AUTHORITY_SHA256,
        "font": repo_path(FONT),
        "font_sha256": FONT_SHA256,
        "title_font": repo_path(TITLE_FONT),
        "title_font_sha256": TITLE_FONT_SHA256,
        "body_font_size_native": BODY_FONT_SIZE,
        "popup_font_size_native": POPUP_FONT_SIZE,
        "title_font_size_native": TITLE_FONT_SIZE,
        "label_text_effects_native": [[list(offset), list(fill)] for offset, fill in LABEL_TEXT_EFFECTS],
        "value_text_effects_native": [[list(offset), list(fill)] for offset, fill in VALUE_TEXT_EFFECTS],
        "title_text_effects_native": [[list(offset), list(fill)] for offset, fill in TITLE_TEXT_EFFECTS],
        "row_baselines_native": list(ROW_BASELINES),
        "row_gaps_native": [ROW_BASELINES[1] - ROW_BASELINES[0], ROW_BASELINES[2] - ROW_BASELINES[1]],
        "assembly_resolution": list(NATIVE_SIZE),
        "review_resolution": list(REVIEW_SIZE),
        "open_native_resolution": list(OPEN_NATIVE_SIZE),
        "open_review_resolution": list(OPEN_REVIEW_SIZE),
        "review_resampling": "nearest for text and shell; byte-exact full-resolution source overlays for named controls",
        "source_normalization_resampling": "complete 1088x504 source reduced once to 272x126 with nearest-neighbor before Assembly",
        "complete_source_horizontally_resampled_during_widening": False,
        "native_shell_extension": {"insert_at": INSERT_AT, "insert_width": INSERT_WIDTH, "method": "exact halves plus nearest-neighbor center donor strip"},
        "exterior_edge_cleanup": "clean native rounded silhouette outside exact inner frame caps",
        "exact_native_source_pixels": exact_results,
        "full_resolution_source_control_overlays": True,
        "strict_exact_preservation_claim": False,
        "mask_comparison_baseline": "deterministic native widened shell",
        "native_edit_mask_pixels": count_pixels(declared),
        "changed_pixels": count_pixels(actual),
        "changed_pixels_outside_native_edit_mask": count_pixels(outside),
        "actual_is_subset_of_native_edit_mask": outside.getbbox() is None,
        "open_mask_comparison_baseline": "closed candidate on transparent 336x196 canvas",
        "open_native_edit_mask_pixels": count_pixels(open_declared),
        "open_changed_pixels": count_pixels(open_actual),
        "open_changed_pixels_outside_native_edit_mask": count_pixels(open_outside),
        "open_actual_is_subset_of_native_edit_mask": open_outside.getbbox() is None,
        "qwen_popup_surface_source": repo_path(QWEN_POPUP_SOURCE),
        "qwen_popup_surface_source_sha256": QWEN_POPUP_SOURCE_SHA256,
        "generated_glyph_pixels_in_final": False,
        "exact_copy": {key: list(value) if isinstance(value, tuple) else value for key, value in EXACT_COPY.items()},
        "closed_native_sha256": sha256(paths["closed_native"]),
        "closed_sha256": sha256(paths["closed"]),
        "open_native_sha256": sha256(paths["open_native"]),
        "open_sha256": sha256(paths["open"]),
        "render_pass": {
            "provider": "openrouter",
            "model": "qwen/qwen-image-3-pro",
            "requested_outputs": 2,
            "completed_outputs": 2,
            "ambiguous_outputs": 0,
            "prompt_id": "e12f195d-dfaa-4810-bac9-96963b4b3c35",
            "usage": "retained masked popup surface only; no generated glyph or closed-state control pixels",
            "new_requests_for_v005": 0,
            "estimated_cost_usd": 0.10,
            "actual_cost_usd": None,
        },
    }
    verification_path = output_dir / "verification.json"
    verification_path.write_text(json.dumps(verification, indent=2) + "\n", encoding="utf-8")
    run = {
        "issue": 138,
        "method": "native-grid widened Assembly with exact source caps and controls",
        "rejected": ["custom-filters-ro-assembly-v001", "custom-filters-ro-assembly-v002", "custom-filters-ro-assembly-v003", "custom-filters-ro-assembly-v004"],
        "outputs": {name: repo_path(path) for name, path in paths.items()},
        "verification": repo_path(verification_path),
        "render_pass": verification["render_pass"],
    }
    (output_dir / "run.json").write_text(json.dumps(run, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(verification, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
