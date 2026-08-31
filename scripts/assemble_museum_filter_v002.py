#!/usr/bin/env python3.12
"""Assemble the Issue #118 final edit from two Qwen v005 donors.

Assembly v001 remains authoritative outside three declared edit families:
the title/header, English lettering, and the object/material tab strip.  The
Qwen candidates are registered to the baseline's magenta frame, reduced to the
client's native 313x211 raster, and copied only through explicit rectangles.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw


NATIVE_SIZE = (313, 211)
SCALE = 4


def magenta_bbox(image: Image.Image) -> tuple[int, int, int, int]:
    """Return an inclusive-looking PIL crop box around the fuchsia frame."""
    pixels = image.convert("RGB")
    xs: list[int] = []
    ys: list[int] = []
    for y in range(pixels.height):
        for x in range(pixels.width):
            red, green, blue = pixels.getpixel((x, y))
            if red > 220 and green < 80 and blue > 180:
                xs.append(x)
                ys.append(y)
    if not xs:
        raise ValueError("image has no detectable magenta window frame")
    return min(xs), min(ys), max(xs) + 1, max(ys) + 1


def register_donor(donor: Image.Image, baseline: Image.Image) -> Image.Image:
    """Register a raw Qwen candidate to the native baseline frame."""
    target_box = magenta_bbox(baseline)
    target_width = target_box[2] - target_box[0]
    target_height = target_box[3] - target_box[1]
    crop = donor.convert("RGB").crop(magenta_bbox(donor))
    crop = crop.resize((target_width, target_height), Image.Resampling.LANCZOS)
    registered = Image.new("RGB", baseline.size, "white")
    registered.paste(crop, target_box[:2])
    return registered


def copy_region(
    output: Image.Image,
    mask: Image.Image,
    donor: Image.Image,
    target_box: tuple[int, int, int, int],
    source_box: tuple[int, int, int, int] | None = None,
) -> None:
    source_box = source_box or target_box
    patch = donor.crop(source_box)
    target_size = (target_box[2] - target_box[0], target_box[3] - target_box[1])
    if patch.size != target_size:
        raise ValueError(f"source {patch.size} does not match target {target_size}")
    output.paste(patch, target_box[:2])
    ImageDraw.Draw(mask).rectangle(
        (target_box[0], target_box[1], target_box[2] - 1, target_box[3] - 1),
        fill=255,
    )


def copy_text_pixels(
    output: Image.Image,
    mask: Image.Image,
    donor: Image.Image,
    target_box: tuple[int, int, int, int],
    source_box: tuple[int, int, int, int],
) -> None:
    """Replace lettering without importing a donor field-background rectangle."""
    patch = donor.crop(source_box)
    target_size = (target_box[2] - target_box[0], target_box[3] - target_box[1])
    if patch.size != target_size:
        raise ValueError(f"source {patch.size} does not match target {target_size}")
    target_background = output.getpixel((target_box[2] - 1, target_box[3] - 1))
    donor_background = patch.getpixel((patch.width - 1, 0))
    ImageDraw.Draw(output).rectangle(
        (target_box[0], target_box[1], target_box[2] - 1, target_box[3] - 1),
        fill=target_background,
    )
    difference = ImageChops.difference(
        patch, Image.new("RGB", patch.size, donor_background)
    ).convert("L")
    glyph_mask = difference.point(lambda value: 255 if value > 3 else 0)
    output.paste(patch, target_box[:2], glyph_mask)
    ImageDraw.Draw(mask).rectangle(
        (target_box[0], target_box[1], target_box[2] - 1, target_box[3] - 1),
        fill=255,
    )


def _scaled(box: tuple[int, int, int, int], scale: int) -> tuple[int, int, int, int]:
    return tuple(value * scale for value in box)  # type: ignore[return-value]


def assemble(
    baseline: Image.Image,
    header_donor: Image.Image,
    text_donor: Image.Image,
) -> tuple[Image.Image, Image.Image, int]:
    if baseline.width % NATIVE_SIZE[0] or baseline.height % NATIVE_SIZE[1]:
        raise ValueError(f"baseline {baseline.size} is not an integer native-scale image")
    scale_x = baseline.width // NATIVE_SIZE[0]
    scale_y = baseline.height // NATIVE_SIZE[1]
    if scale_x != scale_y or scale_x not in (1, SCALE):
        raise ValueError(f"unsupported baseline scale {baseline.size}")
    scale = scale_x
    header = register_donor(header_donor, baseline)
    text = register_donor(text_donor, baseline)
    output = baseline.copy().convert("RGB")
    mask = Image.new("L", baseline.size, 0)

    # Candidate 1 owns the repaired header and title.  The last three native
    # columns in the baseline carried the cyan mismatch the owner identified;
    # replace them with adjacent uninterrupted Qwen glass after the header copy.
    copy_region(output, mask, header, _scaled((3, 3, 310, 23), scale))
    copy_region(
        output,
        mask,
        output,
        _scaled((307, 3, 310, 23), scale),
        _scaled((283, 3, 286, 23), scale),
    )

    # Candidate 2 has the stronger narrow-tab anatomy and stepped inactive tab.
    copy_region(output, mask, text, _scaled((3, 23, 23, 123), scale))

    # Candidate 2's glyphs are copied as native raster pixels.  Rectangles stay
    # clear of every field edge and checkbox so those controls remain byte-for-
    # byte Assembly v001 pixels.
    text_regions = [
        (31, 39, 74, 53),  # Search label
        (31, 66, 72, 80),  # Match label
    ]
    for box in text_regions:
        copy_region(output, mask, text, _scaled(box, scale))

    copy_text_pixels(
        output,
        mask,
        text,
        _scaled((81, 39, 123, 53), scale),
        _scaled((83, 39, 125, 53), scale),
    )
    copy_region(
        output,
        mask,
        text,
        _scaled((90, 66, 116, 80), scale),
        _scaled((92, 66, 118, 80), scale),
    )
    copy_region(
        output,
        mask,
        text,
        _scaled((142, 66, 165, 80), scale),
        _scaled((146, 66, 169, 80), scale),
    )
    copy_region(
        output,
        mask,
        text,
        _scaled((167, 66, 257, 80), scale),
        _scaled((171, 66, 261, 80), scale),
    )

    for row in range(5):
        top = 94 + row * 19
        copy_region(output, mask, text, _scaled((49, top, 147, top + 14), scale))
        # The generated right column sits four native pixels to the right of
        # Assembly v001 after frame registration; shift only its lettering.
        copy_region(
            output,
            mask,
            text,
            _scaled((190, top, 301, top + 14), scale),
            _scaled((194, top, 305, top + 14), scale),
        )

    return output, mask, scale


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--header-donor", type=Path, required=True)
    parser.add_argument("--text-donor", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mask-output", type=Path, required=True)
    args = parser.parse_args()

    baseline = Image.open(args.baseline).convert("RGB")
    header_donor = Image.open(args.header_donor).convert("RGB")
    text_donor = Image.open(args.text_donor).convert("RGB")
    output, mask, scale = assemble(baseline, header_donor, text_donor)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.mask_output.parent.mkdir(parents=True, exist_ok=True)
    if scale == SCALE:
        output.save(args.output)
        output.resize(NATIVE_SIZE, Image.Resampling.BOX).save(
            args.output.with_name(args.output.stem + "-native.png")
        )
        mask.save(args.mask_output)
        mask.resize(NATIVE_SIZE, Image.Resampling.NEAREST).save(
            args.mask_output.with_name(args.mask_output.stem + "-native.png")
        )
    else:
        output.save(args.output.with_name(args.output.stem + "-native.png"))
        output.resize((output.width * SCALE, output.height * SCALE), Image.Resampling.NEAREST).save(
            args.output
        )
        mask.save(args.mask_output.with_name(args.mask_output.stem + "-native.png"))
        mask.resize((mask.width * SCALE, mask.height * SCALE), Image.Resampling.NEAREST).save(
            args.mask_output
        )

    changed = ImageChops.difference(baseline, output)
    changed_pixels = sum(1 for pixel in changed.getdata() if pixel != (0, 0, 0))
    outside = ImageChops.multiply(changed, ImageChops.invert(mask).convert("RGB"))
    outside_changed = sum(1 for pixel in outside.getdata() if pixel != (0, 0, 0))
    outside_max_error = max(max(pixel) for pixel in outside.getdata())
    print(
        f"{args.output} ({args.output.stat().st_size} bytes); "
        f"changed_pixels={changed_pixels}; "
        f"outside_mask_changed_pixels={outside_changed}; "
        f"outside_mask_max_error={outside_max_error}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
