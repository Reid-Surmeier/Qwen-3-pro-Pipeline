#!/usr/bin/env python3
"""Regenerate Issue 34 component-Assembly comparison and objective metrics."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "artifacts/issue-34/component-assembly-v004"
SOURCE = RUN / "source/options-window-source.png"
LAYOUT = RUN / "layout.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _artifact(path: Path, role: str) -> dict[str, Any]:
    record: dict[str, Any] = {
        "path": str(path.relative_to(ROOT)),
        "role": role,
        "sha256": _sha256(path),
    }
    if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
        with Image.open(path) as image:
            record.update(
                {
                    "size": list(image.size),
                    "mode": image.mode,
                }
            )
    return record


def _component_check(
    source: np.ndarray,
    output: np.ndarray,
    source_region: tuple[int, int, int, int],
    target: tuple[int, int],
) -> dict[str, int | bool]:
    x, y, width, height = source_region
    target_x, target_y = target
    expected = source[y : y + height, x : x + width]
    actual = output[target_y : target_y + height, target_x : target_x + width]
    difference = np.abs(expected.astype(np.int16) - actual.astype(np.int16))
    return {
        "byte_identical": bool(np.array_equal(expected, actual)),
        "different_rgba_pixels": int(np.any(difference != 0, axis=2).sum()),
        "max_channel_error": int(difference.max()),
    }


def _region_mask(shape: tuple[int, int], region: tuple[int, ...]) -> np.ndarray:
    x, y, width, height = region
    mask = np.zeros(shape, dtype=bool)
    mask[y : y + height, x : x + width] = True
    return mask


def _metrics(path: Path, normalized_donor: Path, layout: dict[str, Any]) -> dict[str, Any]:
    source = np.asarray(Image.open(SOURCE).convert("RGBA"))
    output = np.asarray(Image.open(path).convert("RGBA"))
    donor = np.asarray(Image.open(normalized_donor).convert("RGBA"))
    edit_region = tuple(layout["final_edit_region"])
    edit_mask = _region_mask(source.shape[:2], edit_region)
    component_mask = np.zeros(source.shape[:2], dtype=bool)
    components: dict[str, dict[str, int | bool]] = {}
    component_kind_counts = {"bgm_slider": 0, "skin_dropdown": 0}
    for component in layout["components"]:
        source_region = tuple(component["source_region"])
        target = tuple(component["target"])
        components[component["name"]] = _component_check(
            source,
            output,
            source_region,
            target,
        )
        component_kind_counts[component["kind"]] += 1
        component_mask |= _region_mask(
            source.shape[:2],
            (target[0], target[1], source_region[2], source_region[3]),
        )
    source_changed = np.any(source != output, axis=2)
    donor_changed = np.any(donor != output, axis=2)
    cleanplate_mask = _region_mask(
        source.shape[:2], tuple(layout["cleanplate"]["target_region"])
    )
    exposed_cleanplate = cleanplate_mask & ~component_mask
    source_owned_margins = edit_mask & ~cleanplate_mask
    cleanplate_rgb = output[exposed_cleanplate, :3].astype(np.int32)
    cleanplate_luminance = (
        2126 * cleanplate_rgb[:, 0]
        + 7152 * cleanplate_rgb[:, 1]
        + 722 * cleanplate_rgb[:, 2]
    ) // 10000
    dark_cleanplate_pixels = int((cleanplate_luminance < 240).sum())
    derived_structural_counts = {
        "bgm_sliders": component_kind_counts["bgm_slider"],
        "effect_rows": 0 if dark_cleanplate_pixels == 0 else None,
        "skin_dropdowns": component_kind_counts["skin_dropdown"],
    }
    return {
        "outside_changed_rgba_pixels": int(source_changed[~edit_mask].sum()),
        "inside_changed_rgba_pixels": int(source_changed[edit_mask].sum()),
        "alpha_changed_pixels": int((source[..., 3] != output[..., 3]).sum()),
        "title_exact": bool(
            np.array_equal(source[45:125, 105:400], output[45:125, 105:400])
        ),
        "footer_japanese_exact": bool(
            np.array_equal(source[560:650, 430:660], output[560:650, 430:660])
        ),
        "components": components,
        "output_structural_check": {
            "derived_counts": derived_structural_counts,
            "expected_counts": layout["expected_structural_counts"],
            "matches_expected": (
                derived_structural_counts == layout["expected_structural_counts"]
            ),
            "exposed_cleanplate_luminance_threshold": 240,
            "exposed_cleanplate_pixels_below_threshold": dark_cleanplate_pixels,
            "minimum_exposed_cleanplate_luminance": int(
                cleanplate_luminance.min()
            ),
            "method": (
                "byte-identical source-component inventory plus a pixel-derived "
                "foreground exclusion check over every exposed clean-plate pixel"
            ),
        },
        "node_induced_change_vs_normalized_donor": {
            "total_changed_rgba_pixels": int(donor_changed.sum()),
            "inside_edit_region_changed_rgba_pixels": int(
                donor_changed[edit_mask].sum()
            ),
            "outside_edit_region_changed_rgb_pixels": int(
                np.any(donor[..., :3] != output[..., :3], axis=2)[~edit_mask].sum()
            ),
            "outside_edit_region_changed_alpha_pixels": int(
                (donor[..., 3] != output[..., 3])[~edit_mask].sum()
            ),
            "source_component_union_changed_rgba_pixels": int(
                donor_changed[component_mask].sum()
            ),
            "exposed_donor_cleanplate_changed_rgba_pixels": int(
                donor_changed[exposed_cleanplate].sum()
            ),
            "source_owned_margin_changed_rgba_pixels": int(
                donor_changed[source_owned_margins].sum()
            ),
        },
    }


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
    return ImageFont.truetype(path, size) if path.exists() else ImageFont.load_default()


def _contact_sheet(items: list[tuple[str, Path]], output: Path) -> None:
    thumb_width, thumb_height, label_height = 786, 359, 52
    canvas = Image.new(
        "RGB",
        (thumb_width * 2, (thumb_height + label_height) * 3),
        "#202124",
    )
    draw = ImageDraw.Draw(canvas)
    font = _font(24)
    for index, (label, path) in enumerate(items):
        x = index % 2 * thumb_width
        y = index // 2 * (thumb_height + label_height)
        image = Image.open(path).convert("RGB")
        image.thumbnail((thumb_width, thumb_height), Image.Resampling.NEAREST)
        image_x = x + (thumb_width - image.width) // 2
        image_y = y + (thumb_height - image.height) // 2
        canvas.paste(image, (image_x, image_y))
        draw.text((x + 12, y + thumb_height + 10), label, fill="white", font=font)
    canvas.save(output)


def main() -> None:
    layout = json.loads(LAYOUT.read_text(encoding="utf-8"))
    raw_renders = [
        RUN / "baseline/raw-render-1.png",
        RUN / "baseline/raw-render-2.png",
    ]
    normalized_donors = [
        RUN / "baseline/normalized-donor-1.png",
        RUN / "baseline/normalized-donor-2.png",
    ]
    outputs = [
        RUN / "outputs/donor-1-component-assembly.png",
        RUN / "outputs/donor-2-component-assembly.png",
    ]
    _contact_sheet(
        [
            ("Reference Screen", SOURCE),
            ("Raw Qwen render 1 (2048 x 1024)", raw_renders[0]),
            ("Component Assembly 1 (same render)", outputs[0]),
            ("Raw Qwen render 2 (2048 x 1024)", raw_renders[1]),
            ("Component Assembly 2 (same render)", outputs[1]),
            (
                "Rejected geometry-only control",
                RUN / "controls/aspect-d1-center.png",
            ),
        ],
        RUN / "comparison-contact-sheet.png",
    )
    record = {
        "schema_version": 1,
        "issue": 34,
        "classification": "qualifying component Assembly pending human visual approval",
        "source": _artifact(SOURCE, "authoritative Reference Screen"),
        "provider": "openrouter",
        "model": "qwen/qwen-image-3-pro",
        "paid_accounting": {
            "cumulative_requested_outputs": 8,
            "cumulative_completed_outputs": 6,
            "confirmed_actual_cost_usd": 0.249,
            "possibly_billed_outputs": 2,
            "new_paid_run_submitted": False,
            "remaining_issue_allowance": 2,
            "runs": [
                {
                    "name": "v001 enlargement",
                    "provider": "openrouter",
                    "model": "qwen/qwen-image-3-pro",
                    "seed": 20260826,
                    "prompt_id": "ba31ea51-05f1-4992-8ab7-148a4668095f",
                    "requested": 2,
                    "completed": 2,
                    "estimated_cost_usd": 0.0845,
                    "actual_cost_usd": 0.083,
                    "evidence": {
                        "pull_request": "https://github.com/Reid-Surmeier/Qwen-3-pro-Pipeline/pull/35",
                        "manifest_path": "artifacts/issue-34/alpha-window-2x/run.json",
                    },
                },
                {
                    "name": "v002 structural edit",
                    "provider": "openrouter",
                    "model": "qwen/qwen-image-3-pro",
                    "seed": 2026082602,
                    "prompt_id": "179dd12b-bd20-430b-a5f3-3f072823c196",
                    "requested": 2,
                    "completed": 2,
                    "estimated_cost_usd": 0.083,
                    "actual_cost_usd": 0.083,
                    "evidence": {
                        "pull_request": "https://github.com/Reid-Surmeier/Qwen-3-pro-Pipeline/pull/37",
                        "manifest_path": "artifacts/issue-34/english-structural-edit-v002/run.json",
                    },
                },
                {
                    "name": "v003 direct baseline",
                    "provider": "openrouter",
                    "model": "qwen/qwen-image-3-pro",
                    "seed": 2026082603,
                    "prompt_id": "e920047d-3ada-47aa-a3bc-be17b5b683c2",
                    "requested": 2,
                    "completed": 2,
                    "estimated_cost_usd": 0.083,
                    "actual_cost_usd": 0.083,
                    "outputs": [
                        _artifact(raw_renders[0], "direct Qwen v003 raw render 1"),
                        _artifact(raw_renders[1], "direct Qwen v003 raw render 2"),
                    ],
                },
                {
                    "name": "v003 focused crop",
                    "provider": "openrouter",
                    "model": "qwen/qwen-image-3-pro",
                    "seed": 2026082603,
                    "prompt_id": "1e8f9909-66df-4555-8276-677c73d0dfa9",
                    "requested": 2,
                    "completed": 0,
                    "estimated_cost_usd": 0.083,
                    "actual_cost_usd": None,
                    "billing": "unknown; counted as spent; never retried",
                },
            ],
        },
        "no_cost_live_runs": [
            {
                "arm": "component Assembly from raw render 1",
                "prompt_id": "b631b7a3-ecc0-4da1-b9b1-43956335f059",
                "status": "success",
                "duration_ms": 201,
            },
            {
                "arm": "component Assembly from raw render 2",
                "prompt_id": "a811e307-5912-4cbb-8f55-11ce55ae5e0b",
                "status": "success",
                "duration_ms": 195,
            },
            {
                "arm": "matched donor normalization control",
                "prompt_id": "571c7f2f-cf45-46ef-846c-e5788a00985f",
                "status": "success",
                "duration_ms": 206,
            },
            {
                "arm": "aspect-normalization control",
                "prompt_id": "7e1a8b86-2bc6-4556-be83-490606b0b9ac",
                "status": "success",
                "duration_ms": 331,
                "finding": "neutral; proportions changed but malformed copy/layout remained",
            },
            {
                "arm": "superseded normalized-input component prototype pair",
                "prompt_ids": [
                    "07624492-0558-4723-b281-3516719c2c99",
                    "4ee63f4a-cc4f-4dc1-88c1-0b2230caf154",
                ],
                "status": "success",
                "finding": "superseded after review required raw-render lineage",
            },
        ],
        "layout": layout,
        "raw_baselines": [
            _artifact(path, f"direct Qwen raw render {index}")
            for index, path in enumerate(raw_renders, start=1)
        ],
        "normalized_donors": [
            _artifact(path, f"nearest-exact normalized donor {index}")
            for index, path in enumerate(normalized_donors, start=1)
        ],
        "outputs": [
            {
                **_artifact(path, f"component Assembly {index}"),
                "checks": _metrics(path, normalized_donors[index - 1], layout),
            }
            for index, path in enumerate(outputs, start=1)
        ],
        "controls": [
            _artifact(RUN / "controls/aspect-d1-stretch.png", "donor 1 stretch"),
            _artifact(RUN / "controls/aspect-d1-center.png", "donor 1 center crop"),
            _artifact(RUN / "controls/aspect-d2-stretch.png", "donor 2 stretch"),
            _artifact(RUN / "controls/aspect-d2-center.png", "donor 2 center crop"),
        ],
        "render_lineage": [
            {
                "raw_render": str(raw_renders[index].relative_to(ROOT)),
                "normalization_workflow": str(
                    (RUN / "workflows/normalization-control.api.json").relative_to(ROOT)
                ),
                "normalized_donor": str(normalized_donors[index].relative_to(ROOT)),
                "component_workflow": str(
                    (RUN / f"workflows/component-donor-{index + 1}.api.json").relative_to(ROOT)
                ),
                "output": str(outputs[index].relative_to(ROOT)),
            }
            for index in range(2)
        ],
        "workflows": [
            _artifact(
                RUN / "workflows/component-donor-1.api.json",
                "executed donor 1 native-node graph",
            ),
            _artifact(
                RUN / "workflows/component-donor-2.api.json",
                "executed donor 2 native-node graph",
            ),
            _artifact(
                RUN / "workflows/normalization-control.api.json",
                "executed raw-render normalization control",
            ),
            _artifact(
                RUN / "workflows/aspect-control.api.json",
                "executed rejected geometry-only graph",
            ),
        ],
        "stopping_reason": (
            "The first ranked no-cost arm visibly repaired the internal copy and "
            "layout on both saved donors, so no remaining paid outputs were used."
        ),
        "human_visual_approval": "required before merge",
    }
    (RUN / "run.json").write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
