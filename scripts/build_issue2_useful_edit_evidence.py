"""Build the Issue #2 useful-edit manifest and human comparison sheet."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


FULL_SOURCE_SHA256 = (
    "c72cd0ec91e6e8490a5549dea015c0e866b126b674a3d255ffff071c06a5ff23"
)
REFERENCE_SHA256 = (
    "7c8e8767f72b72ce4fa4c888507f5ad060003a6cab7802f3e0deef44c8de35d7"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _artifact(path: Path, role: str) -> dict[str, Any]:
    with Image.open(path) as image:
        size = list(image.size)
    return {"path": path.as_posix(), "sha256": _sha256(path), "size": size, "role": role}


def _file_artifact(path: Path, role: str) -> dict[str, Any]:
    return {"path": path.as_posix(), "sha256": _sha256(path), "role": role}


def _font(size: int):
    path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
    return ImageFont.truetype(path.as_posix(), size) if path.exists() else ImageFont.load_default()


def build_contact_sheet(items: list[tuple[str, Path]], output_path: Path) -> None:
    tile_width, image_height, label_height, header_height = 560, 395, 52, 80
    rows = (len(items) + 1) // 2
    sheet = Image.new(
        "RGB",
        (tile_width * 2, header_height + ((image_height + label_height) * rows)),
        (36, 39, 45),
    )
    font = _font(20)
    header_font = _font(13)
    draw = ImageDraw.Draw(sheet)
    draw.text(
        (14, 12),
        f"Full export SHA-256: {FULL_SOURCE_SHA256}",
        fill=(245, 245, 245),
        font=header_font,
    )
    draw.text(
        (14, 42),
        f"Generation crop SHA-256: {REFERENCE_SHA256}",
        fill=(245, 245, 245),
        font=header_font,
    )
    for index, (label, path) in enumerate(items):
        x = (index % 2) * tile_width
        y = header_height + ((index // 2) * (image_height + label_height))
        with Image.open(path) as source:
            image = source.convert("RGB")
        image.thumbnail((tile_width - 24, image_height - 24), Image.Resampling.LANCZOS)
        paste_x = x + (tile_width - image.width) // 2
        paste_y = y + (image_height - image.height) // 2
        sheet.paste(image, (paste_x, paste_y))
        draw.text(
            (x + 14, y + image_height + 14),
            label,
            fill=(245, 245, 245),
            font=font,
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path)


def build_manifest(root: Path, contact_sheet: Path) -> dict[str, Any]:
    source = root / "source/intel-inside-celeron-crop.png"
    source_export = root / "source/intel-inside-source-node-67-710.png"
    guide = root / "fixture/green-selection-guide-v001.png"
    baseline = [root / f"qwen/results/baseline-v001_0000{i}_.png" for i in (1, 2)]
    guided = [root / f"qwen/results/guided-v001_0000{i}_.png" for i in (1, 2)]
    deterministic_baseline = root / "assembly/results/exact-green-v002_00001_.png"
    deterministic_guided = root / "assembly/results/precise-guided-v005_00001_.png"
    fixture = root / "fixture"
    assembly = root / "assembly"
    qwen = root / "qwen"
    return {
        "schema_version": 1,
        "issue": 2,
        "classification": "comparison evidence and reproducibility metadata",
        "source_authority": {
            "full_export": _artifact(source_export, "FigJam node 67:710 source identity and crop provenance"),
            "reference_1": _artifact(source, "only authoritative Qwen image input in both conditions"),
            "forbidden_prior_output_sha256": "d9366592ef73be79aa3a2e202df895a82eea14026bbd551da3e680a38afbe1ab",
            "prior_output_used_in_corrected_test": False,
        },
        "guide": _artifact(guide, "Reference 2 in guided condition only"),
        "selection_masks": {
            "source_letter": _artifact(
                fixture / "source-e-mask-v001.png",
                "selected final source e",
            ),
            "source_region": _artifact(
                fixture / "source-region-mask-v001.png",
                "allowed source removal region",
            ),
            "target_letter": _artifact(
                fixture / "target-e-mask-v001.png",
                "translated e target shape",
            ),
            "target_region": _artifact(
                fixture / "target-region-mask-v001.png",
                "allowed target placement region",
            ),
            "combined_region": _artifact(
                fixture / "combined-region-mask-v001.png",
                "union of allowed source and target regions",
            ),
        },
        "generation": {
            "provider": "openrouter",
            "model": "qwen/qwen-image-3-pro",
            "settings": {"resolution": "1K", "aspect_ratio": "3:2", "count_per_condition": 2, "seed": 20260826},
            "baseline_prompt_id": "ec5370d4-103b-467a-90d0-53393e6e4f44",
            "guided_prompt_id": "d1773803-431d-490b-915d-885d60403354",
            "completed_outputs": 4,
            "actual_cost_usd": 0.169,
            "historical_rejected_cost_usd": 0.255,
            "cumulative_issue_cost_usd": 0.424,
            "effective_issue_output_count_after_run": 10,
            "outputs": [
                _artifact(baseline[0], "baseline candidate 1; requested edit completed"),
                _artifact(baseline[1], "baseline candidate 2; requested edit completed and selected baseline donor"),
                _artifact(guided[0], "guided candidate 1; requested edit completed and selected guided donor"),
                _artifact(guided[1], "guided candidate 2; rejected because source e remained"),
            ],
            "matched_variable": "presence of the green selection guide as Reference 2",
            "finding": "Baseline completed the edit in 2 of 2 outputs; guided completed it in 1 of 2. The guide did not improve generation consistency, but selected guided candidate 1 aligned the relocated e more completely in deterministic Assembly.",
            "workflow_evidence": {
                "plan": _file_artifact(qwen / "plan.json", "paid run plan and cap check"),
                "baseline": _file_artifact(
                    qwen / "baseline-v001.api.json",
                    "source-only Qwen workflow",
                ),
                "guided": _file_artifact(
                    qwen / "guided-v001.api.json",
                    "source-plus-guide Qwen workflow",
                ),
            },
        },
        "assembly": {
            "provider_outputs": 0,
            "selected_baseline": _artifact(deterministic_baseline, "rejected deterministic baseline; target glyph was partial"),
            "selected_guided": _artifact(deterministic_guided, "best bounded deterministic candidate; visible source patch remains"),
            "selected_guided_prompt_id": "237eb308-1bfe-485d-aaf8-c9dc7f133c02",
            "outside_allowed_mask_changed_pixels": 0,
            "allowed_mask_pixels": 6913,
            "nodes_tested": [
                "ImageColorToMask", "ImageToMask", "MaskComposite", "GrowMask", "FeatherMask",
                "RepeatImageBatch", "ImageBlur", "StickerPerspectiveWarp", "ImageCompositeMasked",
                "MaskedReferenceFidelityGate",
            ],
            "options_tested": [
                {"name": "exact green key", "color_integer": 65280},
                {"name": "grown union", "expand": 4, "tapered_corners": True},
                {
                    "name": "feathered union",
                    "allowed_expand": 8,
                    "feather": {"left": 8, "top": 8, "right": 8, "bottom": 8},
                },
                {"name": "source-derived blur", "blur_radius": 31, "sigma": 10.0},
                {
                    "name": "precise source and target",
                    "source_expand": 4,
                    "target_expand": 4,
                    "feather": 4,
                },
            ],
            "experiments": [
                {
                    "revision": 1,
                    "prompt_id": "49c1f29a-c6ae-425c-a455-f064316d0199",
                    "result": "rejected because the destination batch was not repeated",
                    "workflow": _file_artifact(assembly / "workflow.api.json", "rejected v1 workflow"),
                    "plan": _file_artifact(assembly / "experiment-plan.json", "rejected v1 plan"),
                },
                {
                    "revision": 2,
                    "prompt_id": "c52b258f-f458-4e89-894a-4c012084b2a9",
                    "result": "zero outside-mask changes; hard patch edge remained",
                    "workflow": _file_artifact(assembly / "workflow-v002.api.json", "exact-key and grown-union workflow"),
                    "plan": _file_artifact(assembly / "experiment-plan-v002.json", "v2 plan"),
                },
                {
                    "revision": 3,
                    "prompt_id": "0d493a16-4b8e-471a-bf72-f8b55440837d",
                    "result": "zero outside-mask changes; feathered donor patch remained",
                    "workflow": _file_artifact(assembly / "workflow-v003-feather.api.json", "feathered-union workflow"),
                    "plan": _file_artifact(assembly / "experiment-plan-v003.json", "v3 plan"),
                },
                {
                    "revision": 4,
                    "prompt_id": "0c20bc4d-05a7-4ef6-96f3-755a8e2e7fce",
                    "result": "rejected because source blur produced a blue-gray smudge",
                    "workflow": _file_artifact(assembly / "workflow-v004-final.api.json", "source-blur workflow"),
                    "plan": _file_artifact(assembly / "experiment-plan-v004.json", "v4 plan"),
                },
                {
                    "revision": 5,
                    "prompt_id": "237eb308-1bfe-485d-aaf8-c9dc7f133c02",
                    "result": "best bounded candidate; visible texture patch remains",
                    "workflow": _file_artifact(assembly / "workflow-v005-precise.api.json", "precise-mask workflow"),
                    "plan": _file_artifact(assembly / "experiment-plan-v005.json", "v5 plan"),
                },
            ],
            "limitation": "Exact ownership passed, but donor/source texture mismatch remains visible at the removed glyph. This candidate is evidence, not an approved final.",
        },
        "contact_sheet": _artifact(contact_sheet, "human comparison evidence"),
        "human_visual_approval": "pending",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    contact_sheet = args.root / "useful-edit-comparison-v001.png"
    items = [
        ("Full source export — FigJam 67:710", args.root / "source/intel-inside-source-node-67-710.png"),
        ("Authoritative source crop — Reference 1", args.root / "source/intel-inside-celeron-crop.png"),
        ("Green selection guide — Reference 2", args.root / "fixture/green-selection-guide-v001.png"),
        ("Baseline 1 — edit completed", args.root / "qwen/results/baseline-v001_00001_.png"),
        ("Baseline 2 — selected donor", args.root / "qwen/results/baseline-v001_00002_.png"),
        ("Guided 1 — selected donor", args.root / "qwen/results/guided-v001_00001_.png"),
        ("Guided 2 — source e remained", args.root / "qwen/results/guided-v001_00002_.png"),
        ("Baseline Assembly — partial target", args.root / "assembly/results/exact-green-v002_00001_.png"),
        ("Guided Assembly — patch still visible", args.root / "assembly/results/precise-guided-v005_00001_.png"),
    ]
    build_contact_sheet(items, contact_sheet)
    manifest = build_manifest(args.root, contact_sheet)
    (args.root / "run.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
