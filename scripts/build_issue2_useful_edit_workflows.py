"""Build the matched source-only and source-plus-guide workflows for Issue #2."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from qwen_ui_pipeline import (
    build_comfyui_api_workflow,
    build_comfyui_mask_reference_workflow,
)


SOURCE_EXPORT_SHA256 = (
    "c72cd0ec91e6e8490a5549dea015c0e866b126b674a3d255ffff071c06a5ff23"
)
REFERENCE_SHA256 = (
    "7c8e8767f72b72ce4fa4c888507f5ad060003a6cab7802f3e0deef44c8de35d7"
)
REFERENCE_FILENAME = "issue-2/useful-edit/intel-inside-celeron-crop-v001.png"
GUIDE_FILENAME = "issue-2/useful-edit/green-selection-guide-v001.png"
SEED = 20260826

EDIT_BRIEF: dict[str, Any] = {
    "provider": "openrouter",
    "model": "qwen/qwen-image-3-pro",
    "objective": (
        "Perform one surgical edit on Reference 1. Move only the final lowercase "
        "e from the lower word inside the blue oval to the empty left-center of "
        "the blue band below. Remove it cleanly from the original word, restore "
        "the pale sticker field behind it, and recolor the moved e opaque white."
    ),
    "reference_role": (
        "Reference 1 is the authoritative original Intel Inside/Celeron source "
        "crop. If Reference 2 is present, it is only a spatial guide: the green "
        "halo marks the source e and the green e on the blue band marks the exact "
        "destination. Never copy green into the output."
    ),
    "preservation_invariants": [
        "Preserve the complete crop, camera perspective, blur, lighting, print texture, and resolution character.",
        "Preserve the Intel oval, every other Intel Inside letter, Celeron word and registered mark, blue band, and white M.",
        "Do not redraw, straighten, sharpen, upscale, recrop, translate, or redesign the sticker.",
    ],
    "canvas": [
        "Keep the same landscape composition and include the full original crop.",
        "The only editable areas are the marked source e and its marked destination on the blue band.",
    ],
    "regions": [
        {
            "name": "final lowercase e in the lower word inside the oval",
            "change": (
                "Remove that e so the remaining lower word reads insid. Fill the "
                "vacated glyph area with the matching pale photographed sticker field."
            ),
            "preserve": ["the preceding d", "the surrounding blue oval", "all other letters"],
        },
        {
            "name": "empty left-center area of the lower blue band",
            "change": (
                "Place one lowercase e there at the guide position. Match the "
                "source glyph's italic shape, scale, orientation, blur, and print "
                "texture, but render the moved glyph white."
            ),
            "preserve": ["the blue band geometry", "the existing white M"],
        },
    ],
    "exact_copy": [
        {"region": "upper word inside oval", "text": "intel"},
        {"region": "lower word remaining inside oval", "text": "insid"},
        {"region": "processor line", "text": "celeron"},
        {"region": "lower blue band right side", "text": "M"},
        {"region": "moved glyph on lower blue band", "text": "e"},
    ],
    "style": [
        "Unretouched low-resolution photograph of the original OEM laptop sticker.",
        "Keep the existing soft focus and perspective instead of creating clean vector art.",
    ],
    "asset_rules": [
        "Use only the original source crop as artwork authority.",
        "A second image, when present, is a selection guide rather than replacement artwork.",
    ],
    "negative_constraints": [
        "No green pixels, guide outline, arrow, box, or selection mark in the output.",
        "No new logo, icon, word, letter, shadow, border, or background.",
        "No duplicate e and no change to the existing M.",
        "No reinterpretation of the original source as a clean modern sticker.",
    ],
    "quality_checks": [
        "The final e is absent from its original position and appears exactly once on the blue band in white.",
        "The preceding letters remain in place and the blue oval remains continuous.",
        "Everything outside the two declared regions remains visually unchanged.",
    ],
    "output": {
        "resolution": "1K",
        "aspect_ratio": "3:2",
        "count": 2,
        "seed": SEED,
    },
}


def build_workflows() -> tuple[dict[str, Any], dict[str, Any]]:
    baseline = build_comfyui_api_workflow(
        EDIT_BRIEF,
        reference_filename=REFERENCE_FILENAME,
        filename_prefix="issue-2/useful-edit/qwen/baseline-v001",
    )
    baseline["4"] = {
        "class_type": "SaveText",
        "inputs": {
            "text": ["2", 1],
            "filename_prefix": "issue-2/useful-edit/qwen/baseline-v001-metadata",
            "format": "json",
        },
    }
    guided = build_comfyui_mask_reference_workflow(
        EDIT_BRIEF,
        reference_filename=REFERENCE_FILENAME,
        mask_guide_filename=GUIDE_FILENAME,
        filename_prefix="issue-2/useful-edit/qwen/guided-v001",
    )
    if baseline["2"]["inputs"]["edit_brief_json"] != guided["4"]["inputs"][
        "edit_brief_json"
    ]:
        raise ValueError("Matched workflows do not contain the same Edit Brief")
    return baseline, guided


def build_plan() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "issue": 2,
        "classification": "comparison evidence plan",
        "source_export": {
            "path": "artifacts/issue-2/useful-edit/source/intel-inside-source-node-67-710.png",
            "sha256": SOURCE_EXPORT_SHA256,
            "role": "source identity and crop provenance; not a Qwen input",
        },
        "reference_1": {
            "path": "artifacts/issue-2/useful-edit/source/intel-inside-celeron-crop.png",
            "sha256": REFERENCE_SHA256,
            "comfyui_filename": REFERENCE_FILENAME,
            "role": "authoritative Qwen input in both conditions",
        },
        "guide": {
            "path": "artifacts/issue-2/useful-edit/fixture/green-selection-guide-v001.png",
            "comfyui_filename": GUIDE_FILENAME,
            "role": "additional visual reference in the guided condition only",
        },
        "forbidden_generation_input": {
            "path": "artifacts/issue-2/qualification/issue-2-truth-social-inside-sticker-v001.png",
            "sha256": "d9366592ef73be79aa3a2e202df895a82eea14026bbd551da3e680a38afbe1ab",
            "reason": "prior generated output, not a source image",
        },
        "matched_variable": "presence of Reference 2 green selection guide",
        "settings": EDIT_BRIEF["output"],
        "provider": EDIT_BRIEF["provider"],
        "model": EDIT_BRIEF["model"],
        "allowance": {
            "effective_issue_cap": 10,
            "completed_before_corrected_test": 6,
            "planned_outputs": 4,
            "maximum_after_plan": 10,
        },
        "cost": {
            "pre_submission_estimate_usd": 0.17,
            "basis": "four outputs at the prior six-output average of $0.0425 each",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-directory", type=Path, required=True)
    args = parser.parse_args()
    baseline, guided = build_workflows()
    args.output_directory.mkdir(parents=True, exist_ok=True)
    files = {
        "baseline-v001.api.json": baseline,
        "guided-v001.api.json": guided,
        "plan.json": build_plan(),
    }
    for filename, value in files.items():
        (args.output_directory / filename).write_text(
            json.dumps(value, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
