"""Build the controlled Japanese-preserving node experiment for Issue #34."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

from PIL import Image, ImageDraw, ImageFont

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from qwen_ui_pipeline.prompt_manifest import compile_edit_brief
from qwen_ui_pipeline.comfyui_workflow import build_comfyui_assembly_workflow


SOURCE_SHA256 = (
    "7132ec99366fe2c33a1db5cadd92448257e35795764f4010b808e06723a40b16"
)
SOURCE_SIZE = (1572, 718)
BASELINE_COMMIT = "37c87b8a071c1ab8bd15f0d0c55dfd8a59b3de43"
CANDIDATE_COMMIT = "d25cf4f27e81ab8b8a61d4869a07da3683cc3ff1"
SEED = 2026082603
CONTEXT_RECT = (160, 64, 1250, 625)
EDIT_RECT = (160, 130, 1250, 395)
DONOR_RECT = (0, 66, 1250, 395)
ASSEMBLY_RECT = (160, 130, 1350, 350)
FEATHER_PIXELS = 16
EXPERIMENT_ROOT = Path("artifacts/issue-34/japanese-node-experiment-v003")
SOURCE_PATH = Path(
    "artifacts/issue-34/alpha-window-2x/source/options-window-source.png"
)


def build_japanese_edit_brief() -> dict[str, Any]:
    """Describe one fixed-canvas edit while locking source-owned Japanese copy."""

    return {
        "provider": "openrouter",
        "model": "qwen/qwen-image-3-pro",
        "objective": (
            "Edit this same Japanese options window on the same fixed canvas. "
            "Remove the complete Effect row and close its gap by reflowing the "
            "remaining controls. Keep exactly one BGM slider and one Skin dropdown."
        ),
        "reference_role": (
            "The supplied image is the immutable Reference Screen and the authority "
            "for the pixel-era raster style, geometry, colors, controls, and states."
        ),
        "preservation_invariants": [
            "Keep the complete window on the same canvas with no crop or surrounding scene.",
            "Keep the original Japanese title and bottom label character-for-character.",
            "Keep the magenta frame, blue-grey title bar, tabs, BGM state, Skin dropdown, bottom checkbox states, bevels, borders, shadows, and transparent exterior.",
            "Keep the original aliased pixel scale and limited palette; do not modernize, vectorize, or redesign the interface.",
        ],
        "regions": [
            {
                "name": "Effect row",
                "change": (
                    "Remove its label, left and right arrows, slider track, handle, "
                    "checkbox, and adjacent on label."
                ),
            },
            {
                "name": "remaining body controls",
                "change": (
                    "Reflow BGM and Skin vertically into the removed row's space with "
                    "uniform spacing and no empty Effect-shaped band."
                ),
            },
        ],
        "exact_copy": [
            {"region": "title bar", "text": "オプション"},
            {"region": "left tab", "text": "option"},
            {"region": "left tab", "text": "info"},
            {"region": "remaining slider", "text": "BGM"},
            {"region": "dropdown", "text": "Skin"},
            {"region": "bottom option", "text": "スナップ"},
        ],
        "asset_rules": [
            "Return exactly one complete options window per output.",
            "Use no guide color, annotation, selection outline, invented icon, or extra reference content.",
            "Keep the original Japanese copy; do not convert any text to another language.",
        ],
        "negative_constraints": [
            "No Effect label, second slider, second arrow pair, second handle, second checkbox, or second on label.",
            "No empty horizontal band where the Effect row was removed.",
            "No duplicate BGM control, duplicate Skin control, extra control row, or new text.",
            "No green guide, mask color, highlight, selection rectangle, glow, or annotation.",
        ],
        "quality_checks": [
            "The complete Effect row is absent.",
            "Exactly one BGM slider and one Skin dropdown remain.",
            "The retained controls use even vertical spacing and preserve their original states.",
            "The window remains recognizably the same Japanese pixel-era interface.",
        ],
        "output": {
            "resolution": "2K",
            "aspect_ratio": "2:1",
            "count": 2,
            "seed": SEED,
        },
    }


def _crop_region(rectangle: tuple[int, int, int, int]) -> dict[str, int]:
    x, y, width, height = rectangle
    return {"x": x, "y": y, "width": width, "height": height}


def build_direct_baseline_workflow(
    brief: dict[str, Any],
    *,
    reference_filename: str,
) -> dict[str, Any]:
    """Build the no-helper baseline against the complete Reference Screen."""

    return {
        "1": {
            "class_type": "LoadImage",
            "inputs": {"image": reference_filename},
        },
        "2": {
            "class_type": "QwenImage3Render",
            "inputs": {
                "edit_brief_json": json.dumps(
                    brief,
                    ensure_ascii=False,
                    sort_keys=True,
                ),
                "reference_images": ["1", 0],
            },
        },
        "3": {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": "issue-34/japanese-v003/baseline/raw",
                "images": ["2", 0],
            },
        },
        "4": {
            "class_type": "SaveText",
            "inputs": {
                "filename_prefix": "issue-34/japanese-v003/baseline/metadata",
                "format": "json",
                "text": ["2", 1],
            },
        },
    }


def build_focused_crop_workflow(
    brief: dict[str, Any],
    *,
    reference_filename: str,
) -> dict[str, Any]:
    """Crop before Qwen, then hard- and feather-composite the same donor batch."""

    resize_inputs = {
        "resize_type": "scale dimensions",
        "resize_type.width": CONTEXT_RECT[2],
        "resize_type.height": CONTEXT_RECT[3],
        "resize_type.crop": "disabled",
        "scale_method": "lanczos",
    }
    composite_inputs = {
        "destination": ["1", 0],
        "source": ["6", 0],
        "x": EDIT_RECT[0],
        "y": EDIT_RECT[1],
        "resize_source": False,
    }
    return {
        "1": {
            "class_type": "LoadImage",
            "inputs": {"image": reference_filename},
        },
        "2": {
            "class_type": "ImageCropV2",
            "inputs": {
                "image": ["1", 0],
                "crop_region": _crop_region(CONTEXT_RECT),
            },
        },
        "3": {
            "class_type": "QwenImage3Render",
            "inputs": {
                "edit_brief_json": json.dumps(
                    brief,
                    ensure_ascii=False,
                    sort_keys=True,
                ),
                "reference_images": ["2", 0],
            },
        },
        "4": {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": "issue-34/japanese-v003/focused/raw",
                "images": ["3", 0],
            },
        },
        "5": {
            "class_type": "ResizeImageMaskNode",
            "inputs": {"input": ["3", 0], **resize_inputs},
        },
        "6": {
            "class_type": "ImageCropV2",
            "inputs": {
                "image": ["5", 0],
                "crop_region": _crop_region(DONOR_RECT),
            },
        },
        "7": {
            "class_type": "SolidMask",
            "inputs": {
                "value": 1.0,
                "width": EDIT_RECT[2],
                "height": EDIT_RECT[3],
            },
        },
        "8": {
            "class_type": "FeatherMask",
            "inputs": {
                "mask": ["7", 0],
                "left": FEATHER_PIXELS,
                "top": FEATHER_PIXELS,
                "right": FEATHER_PIXELS,
                "bottom": FEATHER_PIXELS,
            },
        },
        "9": {
            "class_type": "ImageCompositeMasked",
            "inputs": {**composite_inputs, "mask": ["7", 0]},
        },
        "10": {
            "class_type": "ImageCompositeMasked",
            "inputs": {**composite_inputs, "mask": ["8", 0]},
        },
        "11": {
            "class_type": "MaskToImage",
            "inputs": {"mask": ["8", 0]},
        },
        "12": {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": "issue-34/japanese-v003/focused/hard",
                "images": ["9", 0],
            },
        },
        "13": {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": "issue-34/japanese-v003/focused/feathered",
                "images": ["10", 0],
            },
        },
        "14": {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": "issue-34/japanese-v003/focused/mask",
                "images": ["11", 0],
            },
        },
        "15": {
            "class_type": "SaveText",
            "inputs": {
                "filename_prefix": "issue-34/japanese-v003/focused/metadata",
                "format": "json",
                "text": ["3", 1],
            },
        },
    }


def build_baseline_assembly_workflow(
    *,
    candidate_filename: str,
    reference_filename: str,
    candidate_number: int,
    rectangle: tuple[int, int, int, int] = ASSEMBLY_RECT,
    output_version: str = "assembly-v3",
    rejoin_reference_alpha: bool = True,
) -> dict[str, Any]:
    """Apply hard and feathered region Assembly to one successful baseline donor."""

    composite_inputs = {
        "destination": ["1", 0],
        "source": ["4", 0],
        "x": rectangle[0],
        "y": rectangle[1],
        "resize_source": False,
    }
    prefix = f"issue-34/japanese-v003/{output_version}/candidate-{candidate_number:02d}"
    workflow = {
        "1": {
            "class_type": "LoadImage",
            "inputs": {"image": reference_filename},
        },
        "2": {
            "class_type": "LoadImage",
            "inputs": {"image": candidate_filename},
        },
        "3": {
            "class_type": "ResizeImageMaskNode",
            "inputs": {
                "input": ["2", 0],
                "resize_type": "scale dimensions",
                "resize_type.width": SOURCE_SIZE[0],
                "resize_type.height": SOURCE_SIZE[1],
                "resize_type.crop": "disabled",
                "scale_method": "lanczos",
            },
        },
        "4": {
            "class_type": "ImageCropV2",
            "inputs": {
                "image": ["3", 0],
                "crop_region": _crop_region(rectangle),
            },
        },
        "5": {
            "class_type": "SolidMask",
            "inputs": {
                "value": 1.0,
                "width": rectangle[2],
                "height": rectangle[3],
            },
        },
        "6": {
            "class_type": "FeatherMask",
            "inputs": {
                "mask": ["5", 0],
                "left": FEATHER_PIXELS,
                "top": FEATHER_PIXELS,
                "right": FEATHER_PIXELS,
                "bottom": FEATHER_PIXELS,
            },
        },
        "7": {
            "class_type": "ImageCompositeMasked",
            "inputs": {**composite_inputs, "mask": ["5", 0]},
        },
        "8": {
            "class_type": "ImageCompositeMasked",
            "inputs": {**composite_inputs, "mask": ["6", 0]},
        },
        "11": {
            "class_type": "MaskToImage",
            "inputs": {"mask": ["6", 0]},
        },
        "12": {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": f"{prefix}/normalized-baseline",
                "images": ["3", 0],
            },
        },
        "13": {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": f"{prefix}/hard",
                "images": ["9", 0] if rejoin_reference_alpha else ["7", 0],
            },
        },
        "14": {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": f"{prefix}/feathered",
                "images": ["10", 0] if rejoin_reference_alpha else ["8", 0],
            },
        },
        "15": {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": f"{prefix}/mask",
                "images": ["11", 0],
            },
        },
    }
    if rejoin_reference_alpha:
        workflow["9"] = {
            "class_type": "JoinImageWithAlpha",
            "inputs": {"image": ["7", 0], "alpha": ["1", 1]},
        }
        workflow["10"] = {
            "class_type": "JoinImageWithAlpha",
            "inputs": {"image": ["8", 0], "alpha": ["1", 1]},
        }
    return workflow


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def analyze_file(path: Path) -> dict[str, Any]:
    """Record stable identity for one evidence file."""

    payload = path.read_bytes()
    return {
        "path": path.as_posix(),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "bytes": len(payload),
    }


def analyze_image(path: Path) -> dict[str, Any]:
    """Record stable identity and basic raster properties for one artifact."""

    with Image.open(path) as opened:
        size = list(opened.size)
        mode = opened.mode
    return {
        **analyze_file(path),
        "size": size,
        "mode": mode,
    }


def compare_declared_region(
    source_path: Path,
    candidate_path: Path,
    rectangle: tuple[int, int, int, int],
) -> dict[str, int | list[int]]:
    """Count RGBA changes inside and outside one declared edit rectangle."""

    with Image.open(source_path) as opened:
        source = opened.convert("RGBA")
    with Image.open(candidate_path) as opened:
        candidate = opened.convert("RGBA")
    if candidate.size != source.size:
        raise ValueError(
            f"candidate size {candidate.size} does not match source {source.size}"
        )

    x, y, width, height = rectangle
    if x < 0 or y < 0 or x + width > source.width or y + height > source.height:
        raise ValueError(f"rectangle {rectangle} is outside source size {source.size}")

    outside_rgba = 0
    outside_rgb = 0
    outside_alpha = 0
    inside_rgba = 0
    max_outside_delta = 0
    source_pixels = source.load()
    candidate_pixels = candidate.load()
    assert source_pixels is not None
    assert candidate_pixels is not None
    for pixel_y in range(source.height):
        for pixel_x in range(source.width):
            source_pixel = source_pixels[pixel_x, pixel_y]
            candidate_pixel = candidate_pixels[pixel_x, pixel_y]
            channel_delta = tuple(
                abs(source_value - candidate_value)
                for source_value, candidate_value in zip(
                    source_pixel,
                    candidate_pixel,
                    strict=True,
                )
            )
            changed_rgba = any(channel_delta)
            is_inside = (
                x <= pixel_x < x + width and y <= pixel_y < y + height
            )
            if is_inside:
                inside_rgba += int(changed_rgba)
                continue
            outside_rgba += int(changed_rgba)
            outside_rgb += int(any(channel_delta[:3]))
            outside_alpha += int(channel_delta[3] != 0)
            max_outside_delta = max(max_outside_delta, *channel_delta)

    return {
        "rectangle": list(rectangle),
        "outside_rgba_changed_pixels": outside_rgba,
        "outside_rgb_changed_pixels": outside_rgb,
        "outside_alpha_changed_pixels": outside_alpha,
        "inside_rgba_changed_pixels": inside_rgba,
        "max_outside_channel_delta": max_outside_delta,
    }


def _contact_sheet_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for candidate in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    ):
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def build_contact_sheet(
    items: list[tuple[str, Path]],
    output_path: Path,
) -> None:
    """Build one plain-language visual comparison without changing source files."""

    columns = 2
    cell_width = 800
    preview_height = 365
    label_height = 58
    rows = (len(items) + columns - 1) // columns
    canvas = Image.new(
        "RGB",
        (columns * cell_width, rows * (preview_height + label_height)),
        (36, 39, 44),
    )
    draw = ImageDraw.Draw(canvas)
    font = _contact_sheet_font(24)
    for index, (label, path) in enumerate(items):
        row, column = divmod(index, columns)
        left = column * cell_width
        top = row * (preview_height + label_height)
        with Image.open(path) as opened:
            preview = opened.convert("RGBA")
        checker = Image.new("RGBA", preview.size, (238, 238, 238, 255))
        checker.alpha_composite(preview)
        checker.thumbnail((cell_width - 20, preview_height - 20))
        preview_left = left + (cell_width - checker.width) // 2
        preview_top = top + (preview_height - checker.height) // 2
        canvas.paste(checker.convert("RGB"), (preview_left, preview_top))
        draw.text(
            (left + 12, top + preview_height + 10),
            label,
            fill=(245, 245, 245),
            font=font,
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path)


def build_edit_region_audit(
    source_path: Path,
    output_path: Path,
    rectangle: tuple[int, int, int, int],
) -> None:
    """Show the declared region for review; this image is never sent to Qwen."""

    with Image.open(source_path) as opened:
        source = opened.convert("RGBA")
    x, y, width, height = rectangle
    tint = Image.new("RGBA", source.size, (0, 0, 0, 0))
    tint_draw = ImageDraw.Draw(tint)
    tint_draw.rectangle(
        (x, y, x + width - 1, y + height - 1),
        fill=(255, 170, 0, 80),
        outline=(255, 120, 0, 255),
        width=6,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    Image.alpha_composite(source, tint).save(output_path)


def finalize_experiment(root: Path = EXPERIMENT_ROOT) -> dict[str, Any]:
    """Write measured evidence after the bounded live experiment has completed."""

    baseline_paths = [
        root / "baseline/raw_00001_.png",
        root / "baseline/raw_00002_.png",
    ]
    winner_paths = [
        root / "winner/candidate-01_00001_.png",
        root / "winner/candidate-02_00001_.png",
    ]
    matched_donor_paths = [
        root / "matched-donor/candidate-01_00001_.png",
        root / "matched-donor/candidate-02_00001_.png",
    ]
    required = [SOURCE_PATH, *baseline_paths, *matched_donor_paths, *winner_paths]
    missing = [path.as_posix() for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"missing experiment artifacts: {missing}")

    winners = []
    for path, matched_donor_path in zip(
        winner_paths,
        matched_donor_paths,
        strict=True,
    ):
        comparison = compare_declared_region(SOURCE_PATH, path, ASSEMBLY_RECT)
        qualifies = (
            comparison["outside_rgba_changed_pixels"] == 0
            and comparison["inside_rgba_changed_pixels"] > 0
        )
        winners.append(
            {
                **analyze_image(path),
                "comparison_to_source": comparison,
                "node_effect_vs_matched_donor": compare_declared_region(
                    matched_donor_path,
                    path,
                    ASSEMBLY_RECT,
                ),
                "qualifies_exact_exterior": qualifies,
            }
        )

    tested_variants = []
    for version, rectangle, result in (
        ("assembly", EDIT_RECT, "rejected: clipped right-side controls"),
        ("assembly-v2", ASSEMBLY_RECT, "rejected: source alpha was dropped"),
        (
            "assembly-v3",
            ASSEMBLY_RECT,
            "rejected: alpha rejoin still changed source alpha values",
        ),
    ):
        for candidate_number in (1, 2):
            for blend in ("hard", "feathered"):
                path = (
                    root
                    / version
                    / f"candidate-{candidate_number:02d}"
                    / f"{blend}_00001_.png"
                )
                tested_variants.append(
                    {
                        "version": version,
                        "candidate": candidate_number,
                        "blend": blend,
                        "result": (
                            "rejected: visible horizontal seam"
                            if blend == "feathered"
                            else result
                        ),
                        **analyze_image(path),
                        "comparison_to_source": compare_declared_region(
                            SOURCE_PATH,
                            path,
                            rectangle,
                        ),
                    }
                )
    contact_sheet_path = root / "comparison-contact-sheet.png"
    edit_region_audit_path = root / "edit-region-audit.png"
    build_edit_region_audit(SOURCE_PATH, edit_region_audit_path, ASSEMBLY_RECT)
    representative_feather = (
        root / "assembly-v2/candidate-01/feathered_00001_.png"
    )
    sheet_items = [
        ("Original source - Japanese remains authoritative", SOURCE_PATH),
        ("No-node baseline 1 - edit works, whole screen drifts", baseline_paths[0]),
        ("Node result 1 - source outside, edited controls inside", winner_paths[0]),
        ("No-node baseline 2 - second independent donor", baseline_paths[1]),
        ("Node result 2 - repeats the same preservation", winner_paths[1]),
    ]
    if representative_feather.exists():
        sheet_items.append(
            ("Rejected feather blend - visible horizontal seam", representative_feather)
        )
    sheet_items.append(
        (
            "Audit overlay only - orange area is replaced, never sent to Qwen",
            edit_region_audit_path,
        )
    )
    build_contact_sheet(sheet_items, contact_sheet_path)

    run = {
        "issue": 34,
        "classification": "comparison evidence",
        "commits": {
            "baseline": BASELINE_COMMIT,
            "candidate": CANDIDATE_COMMIT,
        },
        "source": analyze_image(SOURCE_PATH),
        "provider": "openrouter",
        "model": "qwen/qwen-image-3-pro",
        "seed": SEED,
        "estimated_initial_cost_usd": 0.166,
        "baselines": [analyze_image(path) for path in baseline_paths],
        "matched_donors": [
            analyze_image(path) for path in matched_donor_paths
        ],
        "tested_workflows": [
            analyze_file(path) for path in sorted(root.glob("*.api.json"))
        ],
        "rejected_or_intermediate_variants": tested_variants,
        "paid_runs": [
            {
                "arm": "direct-baseline",
                "prompt_id": "e920047d-3ada-47aa-a3bc-be17b5b683c2",
                "requested_outputs": 2,
                "completed_outputs": 2,
                "status": "success",
                "actual_cost_usd": 0.083,
                "duration_seconds": 76.54,
            },
            {
                "arm": "focused-crop",
                "prompt_id": "1e8f9909-66df-4555-8276-677c73d0dfa9",
                "requested_outputs": 2,
                "completed_outputs": 0,
                "status": "ambiguous_timeout",
                "billing": "unknown; counted as spent; not retried",
                "duration_seconds": 180.352,
            },
        ],
        "no_cost_node_runs": [
            {
                "prompt_id": "a12e535f-a33e-4f9f-977f-c6184a2b3434",
                "candidate": 1,
                "status": "success",
                "duration_ms": 153,
            },
            {
                "prompt_id": "9fdc375a-07b2-4b99-8826-3ccb35954c85",
                "candidate": 2,
                "status": "success",
                "duration_ms": 148,
            },
            {
                "prompt_id": "5de5f1be-828f-47ff-baef-e2aaa468be7b",
                "candidate": 1,
                "role": "full-canvas matched donor control",
                "status": "success",
                "duration_ms": 173,
            },
            {
                "prompt_id": "76bcc00e-be87-41fa-bb65-2848ab2fbac3",
                "candidate": 2,
                "role": "full-canvas matched donor control",
                "status": "success",
                "duration_ms": 141,
            },
        ],
        "visual_adjudication": {
            "baseline": (
                "Both raw Qwen outputs remove the complete Effect row and retain "
                "one BGM slider plus one Skin dropdown, but they redraw the full screen."
            ),
            "winner": (
                "The hard ReferenceRegionComposite keeps the successful generated "
                "control layout only inside the declared rectangle. Candidate 1 has "
                "the more even spacing; both repeat the exact exterior preservation."
            ),
            "rejected": (
                "FeatherMask adds a visible lower horizontal seam. The earlier "
                "JoinImageWithAlpha graph also changed source alpha outside the edit."
            ),
        },
        "winners": winners,
        "selected_candidate": 1,
        "comfyui_workflow_library": {
            "filename": "issue-34-japanese-hard-region-assembly-v003.json",
            "verified_graph": (
                "LoadImage source + LoadImage donor -> ReferenceRegionComposite "
                "with source MASK -> SaveImage"
            ),
            "lock_status": (
                "not generated: MCP process cannot inspect the remote custom_nodes "
                "Git state without COMFYUI_PATH"
            ),
        },
        "contact_sheet": analyze_image(contact_sheet_path),
        "additional_paid_run_submitted": False,
        "stopping_reason": (
            "Two hard region assemblies repeated the intended semantic edit with "
            "zero RGBA changes outside the declared rectangle. Paid testing stopped."
        ),
    }
    _write_json(root / "run.json", run)

    comparison = winners[0]["comparison_to_source"]
    node_effect = winners[0]["node_effect_vs_matched_donor"]
    report = f"""# Issue 34 result: hard region Assembly is the useful node path

The direct Qwen outputs successfully removed the Effect row, but they redrew the whole interface. The implemented node path uses that successful output only as a donor inside `{ASSEMBLY_RECT[0]},{ASSEMBLY_RECT[1]},{ASSEMBLY_RECT[2]},{ASSEMBLY_RECT[3]}` and keeps the original source everywhere else.

## Measured result

- Two independent node outputs completed successfully.
- Baseline commit: `{BASELINE_COMMIT}`; candidate commit: `{CANDIDATE_COMMIT}`.
- Candidate 1 changed {comparison['inside_rgba_changed_pixels']:,} pixels inside the declared edit rectangle.
- Candidate 1 changed **{comparison['outside_rgba_changed_pixels']} RGBA pixels outside** the rectangle.
- Against the matched full-canvas donor, the node restored {node_effect['outside_rgba_changed_pixels']:,} exterior RGBA pixels and changed **{node_effect['inside_rgba_changed_pixels']} pixels inside** the edit rectangle. This isolates the node contribution from Qwen's edit.
- Original Japanese title `オプション` and footer `スナップ` are source-owned, not regenerated.
- Feathered Assembly was rejected because it adds a visible horizontal seam.
- The focused-crop paid arm timed out ambiguously after 180.352 seconds. It was counted as possibly billed and was not retried.
- Confirmed direct-baseline cost: **$0.083**. Focused-crop billing remains unknown.

## What the node changes

`ReferenceRegionComposite` now has an opt-in source-alpha input. It replaces only the chosen rectangle and copies the source alpha exactly outside it. The default workflow behavior is unchanged.

The GUI-auditable workflow is saved in the ComfyUI library as `issue-34-japanese-hard-region-assembly-v003.json`. A read-back confirmed its four-node graph and source-mask connection. A dependency lock could not be generated because the MCP process does not have a local `COMFYUI_PATH`; this is recorded as a limitation, not treated as verification.

Candidate 1 is the selected comparison candidate because its BGM and Skin spacing is more even. Human visual approval is still required before merge.
"""
    (root / "report.md").write_text(report, encoding="utf-8")
    return run


def prepare_experiment(root: Path = EXPERIMENT_ROOT) -> None:
    """Write immutable pre-submission briefs, graphs, and paid boundaries."""

    source = Path(
        "artifacts/issue-34/alpha-window-2x/source/options-window-source.png"
    )
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if digest != SOURCE_SHA256:
        raise RuntimeError(f"Reference Screen SHA-256 mismatch: {digest}")

    brief = build_japanese_edit_brief()
    _write_json(root / "brief.json", brief)
    (root / "prompt.txt").write_text(
        compile_edit_brief(brief).prompt + "\n",
        encoding="utf-8",
    )
    _write_json(
        root / "direct-baseline.api.json",
        build_direct_baseline_workflow(
            brief,
            reference_filename="issue-34-options-window-source.png",
        ),
    )
    _write_json(
        root / "focused-crop.api.json",
        build_focused_crop_workflow(
            brief,
            reference_filename="issue-34-options-window-source.png",
        ),
    )
    for candidate_number in (1, 2):
        for version, rectangle, rejoin_alpha in (
            ("assembly", EDIT_RECT, False),
            ("assembly-v2", ASSEMBLY_RECT, False),
            ("assembly-v3", ASSEMBLY_RECT, True),
        ):
            _write_json(
                root
                / f"tested-{version}-candidate-{candidate_number:02d}.api.json",
                build_baseline_assembly_workflow(
                    candidate_filename=(
                        f"issue-34-japanese-v003-baseline-{candidate_number:02d}.png"
                    ),
                    reference_filename="issue-34-options-window-source.png",
                    candidate_number=candidate_number,
                    rectangle=rectangle,
                    output_version=version,
                    rejoin_reference_alpha=rejoin_alpha,
                ),
            )
        _write_json(
            root / f"baseline-assembly-candidate-{candidate_number:02d}.api.json",
            build_baseline_assembly_workflow(
                candidate_filename=(
                    f"issue-34-japanese-v003-baseline-{candidate_number:02d}.png"
                ),
                reference_filename="issue-34-options-window-source.png",
                candidate_number=candidate_number,
            ),
        )
        _write_json(
            root / f"winning-candidate-{candidate_number:02d}.api.json",
            build_comfyui_assembly_workflow(
                reference_filename="issue-34-options-window-source.png",
                generated_filename=(
                    f"issue-34-japanese-v003-baseline-{candidate_number:02d}.png"
                ),
                region=",".join(str(value) for value in ASSEMBLY_RECT),
                filename_prefix=(
                    "issue-34/japanese-v003/winner/"
                    f"candidate-{candidate_number:02d}"
                ),
                preserve_reference_alpha=True,
            ),
        )
        _write_json(
            root / f"matched-donor-candidate-{candidate_number:02d}.api.json",
            build_comfyui_assembly_workflow(
                reference_filename="issue-34-options-window-source.png",
                generated_filename=(
                    f"issue-34-japanese-v003-baseline-{candidate_number:02d}.png"
                ),
                region=f"0,0,{SOURCE_SIZE[0]},{SOURCE_SIZE[1]}",
                filename_prefix=(
                    "issue-34/japanese-v003/matched-donor/"
                    f"candidate-{candidate_number:02d}"
                ),
            ),
        )
    _write_json(
        root / "plan.json",
        {
            "issue": 34,
            "commits": {
                "baseline": BASELINE_COMMIT,
                "candidate": CANDIDATE_COMMIT,
            },
            "source": {
                "path": str(source),
                "sha256": SOURCE_SHA256,
                "size": list(SOURCE_SIZE),
            },
            "geometry": {
                "context_crop": list(CONTEXT_RECT),
                "edit_rectangle": list(EDIT_RECT),
                "donor_slice": list(DONOR_RECT),
                "baseline_assembly_rectangle_v2": list(ASSEMBLY_RECT),
                "feather_pixels": FEATHER_PIXELS,
            },
            "initial_paid_matrix": [
                {"arm": "direct-baseline", "requested_outputs": 2},
                {"arm": "focused-crop", "requested_outputs": 2},
            ],
            "conditional_paid_matrix": [
                {
                    "arm": "full-source-plus-unmodified-detail-reference",
                    "requested_outputs": 2,
                    "condition": "focused crop does not qualify",
                }
            ],
            "provider": "openrouter",
            "model": "qwen/qwen-image-3-pro",
            "seed": SEED,
            "estimated_initial_cost_usd": 0.166,
            "ambiguous_request_policy": "count as spent; do not retry",
            "stop_rule": (
                "Stop when one method produces a repeatable pre-explained "
                "improvement or after the conditional arm fails."
            ),
        },
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=EXPERIMENT_ROOT,
        help="Evidence output directory",
    )
    parser.add_argument(
        "--finalize",
        action="store_true",
        help="Measure completed outputs and write report/contact-sheet evidence",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    prepare_experiment(args.root)
    if args.finalize:
        finalize_experiment(args.root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
