"""Build and evaluate the Issue #34 alpha-aware 2x experiment."""

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


SOURCE_SHA256 = (
    "7132ec99366fe2c33a1db5cadd92448257e35795764f4010b808e06723a40b16"
)
SOURCE_SIZE = (1572, 718)
TARGET_SIZE = (3144, 1436)


def build_qwen_brief() -> dict[str, Any]:
    """Describe the source-only 2x reconstruction Render Pass."""

    return {
        "provider": "openrouter",
        "model": "qwen/qwen-image-3-pro",
        "objective": (
            "Regenerate the complete Reference Screen as the same transparent "
            "Japanese options window at twice its original visual size. This is "
            "an enlargement and fidelity test, not a redesign."
        ),
        "reference_role": (
            "Reference 1 is the only image input and the authoritative source for "
            "every pixel, string, control, position, color, border, and shadow."
        ),
        "preservation_invariants": [
            "Keep the entire window and every edge visible; do not crop or add a surrounding scene.",
            "Keep the exact window geometry, magenta outer frame, blue-grey title bar, white panel, checker-shadow edge, and transparent exterior.",
            "Keep both sliders, arrow buttons, handles, checkbox positions and states, dropdown, tabs, labels, and spacing unchanged.",
            "Keep the authentic aliased pixel-era raster character; do not modernize, smooth into vector UI, or invent detail.",
        ],
        "canvas": [
            "The source is 1572 by 718 and the review target is exactly 3144 by 1436.",
            "Preserve the full source composition and approximately 2.19 to 1 aspect ratio.",
            "Make controls and lettering twice as large while retaining their relative placement.",
        ],
        "regions": [],
        "exact_copy": [
            {"region": "title bar", "text": "オプション"},
            {"region": "left tabs", "text": "option"},
            {"region": "left tabs", "text": "info"},
            {"region": "first slider label", "text": "BGM"},
            {"region": "second slider label", "text": "Effect"},
            {"region": "dropdown label", "text": "Skin"},
            {"region": "right of first checkbox", "text": "on"},
            {"region": "right of second checkbox", "text": "on"},
            {"region": "bottom option", "text": "opaque"},
            {"region": "bottom option", "text": "スナップ"},
            {"region": "bottom option", "text": "attack"},
            {"region": "bottom option", "text": "skill"},
            {"region": "bottom option", "text": "item"},
        ],
        "style": [
            "Faithful late-1990s or early-2000s Japanese PC game options dialog.",
            "Crisp enlarged raster pixels, restrained bevels, and the original limited palette.",
        ],
        "asset_rules": [
            "Return exactly one complete options window per output.",
            "Use no image other than Reference 1 and add no selection mark or guide.",
        ],
        "negative_constraints": [
            "No green mask, guide, outline, annotation, glow, or highlighted region.",
            "No new words, icons, controls, decoration, background, or content.",
            "No missing, substituted, translated, duplicated, or misspelled text.",
            "No changed slider values, checkbox states, tab selection, or dropdown state.",
        ],
        "quality_checks": [
            "All listed Exact Copy is legible and character-for-character correct.",
            "The raw output preserves the window silhouette, control count, and state.",
            "After exact-size fitting, the authoritative 2x alpha boundary can be reapplied without cutting into the window.",
        ],
        "output": {
            "resolution": "2K",
            "aspect_ratio": "2:1",
            "count": 2,
            "seed": 20260826,
        },
    }


def build_qwen_workflow(
    brief: dict[str, Any],
    *,
    reference_filename: str,
) -> dict[str, Any]:
    """Build the source-only Qwen Render Pass and metadata outputs."""

    return {
        "1": {
            "class_type": "LoadImage",
            "inputs": {"image": reference_filename},
        },
        "2": {
            "class_type": "QwenImage3Render",
            "inputs": {
                "edit_brief_json": json.dumps(brief, ensure_ascii=False, sort_keys=True),
                "reference_images": ["1", 0],
            },
        },
        "3": {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": "issue-34/qwen/source-only-v001",
                "images": ["2", 0],
            },
        },
        "4": {
            "class_type": "SaveText",
            "inputs": {
                "filename_prefix": "issue-34/qwen/source-only-v001-metadata",
                "format": "json",
                "text": ["2", 1],
            },
        },
    }


def build_qwen_exact_alpha_workflow(
    *,
    candidate_filename: str,
    reference_filename: str,
    candidate_number: int,
) -> dict[str, Any]:
    """Fit a raw Qwen output to target size and reapply the source alpha mask."""

    dimension_inputs = {
        "resize_type": "scale dimensions",
        "resize_type.width": TARGET_SIZE[0],
        "resize_type.height": TARGET_SIZE[1],
        "resize_type.crop": "disabled",
    }
    return {
        "1": {
            "class_type": "LoadImage",
            "inputs": {"image": candidate_filename},
        },
        "2": {
            "class_type": "ResizeImageMaskNode",
            "inputs": {
                "input": ["1", 0],
                **dimension_inputs,
                "scale_method": "lanczos",
            },
        },
        "3": {
            "class_type": "LoadImage",
            "inputs": {"image": reference_filename},
        },
        "4": {
            "class_type": "ResizeImageMaskNode",
            "inputs": {
                "input": ["3", 1],
                **dimension_inputs,
                "scale_method": "nearest-exact",
            },
        },
        "5": {
            "class_type": "JoinImageWithAlpha",
            "inputs": {"image": ["2", 0], "alpha": ["4", 0]},
        },
        "6": {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": (
                    f"issue-34/qwen/exact-alpha-v001-candidate-{candidate_number:02d}"
                ),
                "images": ["5", 0],
            },
        },
    }


def build_alpha_resize_workflow(
    *,
    reference_filename: str,
    filename_prefix: str,
    image_method: str,
    mask_method: str = "nearest-exact",
) -> dict[str, Any]:
    """Build the installed native image/mask resize and alpha join graph."""

    if image_method not in {"nearest-exact", "lanczos"}:
        raise ValueError("image_method must be nearest-exact or lanczos")
    if mask_method != "nearest-exact":
        raise ValueError("the authoritative alpha boundary must use nearest-exact")
    return {
        "1": {
            "class_type": "LoadImage",
            "inputs": {"image": reference_filename},
        },
        "2": {
            "class_type": "ResizeImageMaskNode",
            "inputs": {
                "input": ["1", 0],
                "resize_type": "scale by multiplier",
                "resize_type.multiplier": 2.0,
                "scale_method": image_method,
            },
        },
        "3": {
            "class_type": "ResizeImageMaskNode",
            "inputs": {
                "input": ["1", 1],
                "resize_type": "scale by multiplier",
                "resize_type.multiplier": 2.0,
                "scale_method": mask_method,
            },
        },
        "4": {
            "class_type": "JoinImageWithAlpha",
            "inputs": {"image": ["2", 0], "alpha": ["3", 0]},
        },
        "5": {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": filename_prefix,
                "images": ["4", 0],
            },
        },
    }


def build_failed_split_after_load_workflow(
    *,
    reference_filename: str,
    filename_prefix: str,
    image_method: str,
) -> dict[str, Any]:
    """Reproduce the rejected graph that tries to split alpha from loaded RGB."""

    if image_method not in {"nearest-exact", "lanczos"}:
        raise ValueError("image_method must be nearest-exact or lanczos")
    resize_inputs = {
        "resize_type": "scale by multiplier",
        "resize_type.multiplier": 2.0,
    }
    return {
        "1": {"class_type": "LoadImage", "inputs": {"image": reference_filename}},
        "2": {
            "class_type": "SplitImageWithAlpha",
            "inputs": {"image": ["1", 0]},
        },
        "3": {
            "class_type": "ResizeImageMaskNode",
            "inputs": {
                "input": ["2", 0],
                **resize_inputs,
                "scale_method": image_method,
            },
        },
        "4": {
            "class_type": "ResizeImageMaskNode",
            "inputs": {
                "input": ["2", 1],
                **resize_inputs,
                "scale_method": "nearest-exact",
            },
        },
        "5": {
            "class_type": "JoinImageWithAlpha",
            "inputs": {"image": ["3", 0], "alpha": ["4", 0]},
        },
        "6": {
            "class_type": "SaveImage",
            "inputs": {"filename_prefix": filename_prefix, "images": ["5", 0]},
        },
    }


def analyze_rgba(path: Path) -> dict[str, Any]:
    """Return reproducible identity, dimensions, and alpha statistics."""

    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    with Image.open(path) as opened:
        mode = opened.mode
        image = opened.convert("RGBA")
        alpha = image.getchannel("A")
        histogram = alpha.histogram()
        extrema = alpha.getextrema()
        assert extrema is not None
        width, height = image.size
    return {
        "path": path.as_posix(),
        "sha256": digest,
        "size": [width, height],
        "mode": mode,
        "alpha": {
            "min": extrema[0],
            "max": extrema[1],
            "transparent_pixels": histogram[0],
            "opaque_pixels": histogram[255],
            "partial_pixels": (width * height) - histogram[0] - histogram[255],
        },
    }


def compare_to_authoritative_2x(
    source_path: Path,
    candidate_path: Path,
) -> dict[str, Any]:
    """Compare a candidate to a nearest-neighbor 2x source authority."""

    with Image.open(source_path) as opened:
        authority = opened.convert("RGBA").resize(
            TARGET_SIZE,
            Image.Resampling.NEAREST,
        )
    with Image.open(candidate_path) as opened:
        candidate = opened.convert("RGBA")
    if candidate.size != TARGET_SIZE:
        raise ValueError(
            f"candidate must be {TARGET_SIZE[0]}x{TARGET_SIZE[1]}, got "
            f"{candidate.width}x{candidate.height}"
        )
    authority_alpha = authority.getchannel("A").getdata()
    candidate_alpha = candidate.getchannel("A").getdata()
    alpha_pairs = list(zip(authority_alpha, candidate_alpha, strict=True))
    return {
        "changed_rgba_pixels": sum(
            source != output
            for source, output in zip(authority.getdata(), candidate.getdata(), strict=True)
        ),
        "alpha_value_errors": sum(source != output for source, output in alpha_pairs),
        "transparent_membership_errors": sum(
            (source == 0) != (output == 0) for source, output in alpha_pairs
        ),
        "opaque_membership_errors": sum(
            (source == 255) != (output == 255) for source, output in alpha_pairs
        ),
    }


def _font(size: int):
    path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
    return ImageFont.truetype(path.as_posix(), size) if path.exists() else ImageFont.load_default()


def _checker(size: tuple[int, int], square: int = 24) -> Image.Image:
    image = Image.new("RGB", size, (220, 220, 220))
    draw = ImageDraw.Draw(image)
    for y in range(0, size[1], square):
        for x in range(0, size[0], square):
            if ((x // square) + (y // square)) % 2:
                draw.rectangle(
                    (x, y, min(x + square, size[0]), min(y + square, size[1])),
                    fill=(174, 174, 174),
                )
    return image


def build_contact_sheet(items: list[tuple[str, Path]], output_path: Path) -> None:
    """Build a checker-backed comparison that makes transparency visible."""

    tile_width, image_height, label_height, header_height = 1200, 600, 72, 120
    rows = (len(items) + 1) // 2
    sheet = Image.new(
        "RGB",
        (tile_width * 2, header_height + rows * (image_height + label_height)),
        (35, 38, 44),
    )
    draw = ImageDraw.Draw(sheet)
    draw.text((22, 18), "Issue #34 — alpha-aware 2x window experiment", font=_font(34), fill="white")
    draw.text(
        (22, 68),
        f"Source SHA-256: {SOURCE_SHA256}",
        font=_font(20),
        fill=(220, 224, 232),
    )
    for index, (label, path) in enumerate(items):
        x = (index % 2) * tile_width
        y = header_height + (index // 2) * (image_height + label_height)
        canvas = _checker((tile_width - 24, image_height - 24))
        with Image.open(path) as opened:
            image = opened.convert("RGBA")
        image.thumbnail((canvas.width - 28, canvas.height - 28), Image.Resampling.LANCZOS)
        canvas.paste(
            image,
            ((canvas.width - image.width) // 2, (canvas.height - image.height) // 2),
            image,
        )
        sheet.paste(canvas, (x + 12, y + 12))
        draw.text((x + 18, y + image_height + 14), label, font=_font(25), fill="white")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path)


def _artifact(path: Path, role: str) -> dict[str, Any]:
    result = analyze_rgba(path)
    result["role"] = role
    return result


def _file_artifact(path: Path, role: str) -> dict[str, Any]:
    return {
        "path": path.as_posix(),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "role": role,
    }


def finalize_experiment(root: Path) -> None:
    """Write the final comparison, manifest, and plain-language report."""

    source = root / "source/options-window-source.png"
    authoritative = root / "deterministic/authoritative-nearest-2x.png"
    with Image.open(source) as opened:
        opened.convert("RGBA").resize(TARGET_SIZE, Image.Resampling.NEAREST).save(
            authoritative
        )

    failed_split = root / "deterministic/nearest-exact-2x_00001_.png"
    native_nearest = root / "deterministic/nearest-exact-alpha-2x_00001_.png"
    native_lanczos = root / "deterministic/lanczos-alpha-2x_00001_.png"
    raw_1 = root / "qwen/raw/source-only-v001_00001_.png"
    raw_2 = root / "qwen/raw/source-only-v001_00002_.png"
    exact_1 = root / "qwen/exact-alpha/exact-alpha-v001-candidate-01_00001_.png"
    exact_2 = root / "qwen/exact-alpha/exact-alpha-v001-candidate-02_00001_.png"
    required = [
        source,
        failed_split,
        native_nearest,
        native_lanczos,
        raw_1,
        raw_2,
        exact_1,
        exact_2,
    ]
    missing = [path.as_posix() for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"missing experiment output(s): {missing}")

    contact_sheet = root / "comparison-v001.png"
    build_contact_sheet(
        [
            ("Source — 1572 x 718 RGBA", source),
            ("Exact 2x control — nearest-neighbor RGBA", authoritative),
            ("Rejected split-after-load — alpha lost", failed_split),
            ("Native nearest-exact — source MASK used", native_nearest),
            ("Native Lanczos RGB — source MASK used", native_lanczos),
            ("Qwen raw 1 — 2048 x 1024 RGB", raw_1),
            ("Qwen raw 2 — 2048 x 1024 RGB", raw_2),
            ("Qwen 1 — exact size + source MASK", exact_1),
            ("Qwen 2 — exact size + source MASK", exact_2),
        ],
        contact_sheet,
    )

    manifest = {
        "schema_version": 1,
        "issue": 34,
        "classification": "comparison evidence and reproducibility metadata",
        "source": _artifact(source, "immutable Reference Screen and only Qwen input"),
        "target_size": list(TARGET_SIZE),
        "policy": {
            "fixed_repository_cap_removed": True,
            "decision": "ADR 0004",
            "smallest_useful_batch": 2,
            "additional_paid_outputs_requested": 0,
            "stopping_reason": "the initial pair answered the named comparison question",
        },
        "native_alpha_experiment": {
            "failed_split_after_load": {
                "prompt_ids": [
                    "d7d486ba-7ab3-4f57-a788-e555e65fbb44",
                    "fc26f22b-9f27-4dad-bc80-05702841390d",
                ],
                "finding": (
                    "LoadImage output 0 is RGB, so SplitImageWithAlpha could not "
                    "recover the uploaded PNG alpha; both outputs were fully opaque."
                ),
                "nearest_output": _artifact(failed_split, "rejected fully opaque evidence"),
                "workflows": [
                    _file_artifact(
                        root / "deterministic/failed-split-nearest-exact-2x.api.json",
                        "rejected nearest-exact split-after-load graph",
                    ),
                    _file_artifact(
                        root / "deterministic/failed-split-lanczos-2x.api.json",
                        "rejected Lanczos split-after-load graph",
                    ),
                ],
            },
            "corrected_graph": (
                "LoadImage IMAGE -> ResizeImageMaskNode; LoadImage MASK -> "
                "ResizeImageMaskNode; both -> JoinImageWithAlpha"
            ),
            "prompt_ids": {
                "nearest_exact": "a73397d8-4972-439d-99b7-61b7a40793fb",
                "lanczos": "4470001f-1909-4954-8a46-12694baffc29",
            },
            "workflows": [
                _file_artifact(
                    root / "deterministic/nearest-exact-alpha-2x.api.json",
                    "corrected nearest-exact image and source-mask graph",
                ),
                _file_artifact(
                    root / "deterministic/lanczos-alpha-2x.api.json",
                    "corrected Lanczos image and source-mask graph",
                ),
            ],
            "authoritative_control": _artifact(
                authoritative,
                "exact nearest-neighbor 2x control generated outside ComfyUI",
            ),
            "nearest_exact": {
                "artifact": _artifact(native_nearest, "native pixel-art enlargement"),
                "comparison": compare_to_authoritative_2x(source, native_nearest),
                "finding": "RGB is exact; low-alpha fringe precision changes remain.",
            },
            "lanczos": {
                "artifact": _artifact(native_lanczos, "native smoothed enlargement"),
                "comparison": compare_to_authoritative_2x(source, native_lanczos),
                "finding": "RGB is smoothed; the same low-alpha fringe precision changes remain.",
            },
        },
        "qwen_render_pass": {
            "provider": "openrouter",
            "model": "qwen/qwen-image-3-pro",
            "prompt_id": "ba31ea51-05f1-4992-8ab7-148a4668095f",
            "requested_outputs": 2,
            "completed_outputs": 2,
            "pre_submission_estimate_usd": 0.0845,
            "actual_cost_usd": 0.083,
            "settings": {"resolution": "2K", "aspect_ratio": "2:1", "seed": 20260826},
            "usage": {
                "prompt_tokens": 610,
                "completion_tokens": 8350,
                "image_tokens": 8350,
                "total_tokens": 8960,
            },
            "selection_guide_used": False,
            "workflow_evidence": {
                "brief": _file_artifact(root / "qwen/brief.json", "structured Edit Brief"),
                "plan": _file_artifact(root / "qwen/plan.json", "pre-submission plan and estimate"),
                "prompt": _file_artifact(root / "qwen/prompt.txt", "compiled provider prompt"),
                "render": _file_artifact(
                    root / "qwen/source-only-v001.api.json",
                    "source-only paid Render Pass",
                ),
                "exact_alpha": [
                    _file_artifact(
                        root / "qwen/exact-alpha-v001-candidate-01.api.json",
                        "candidate 1 exact-size and source-mask postprocess",
                    ),
                    _file_artifact(
                        root / "qwen/exact-alpha-v001-candidate-02.api.json",
                        "candidate 2 exact-size and source-mask postprocess",
                    ),
                ],
            },
            "raw_outputs": [
                _artifact(raw_1, "source-only raw Qwen candidate 1"),
                _artifact(raw_2, "source-only raw Qwen candidate 2"),
            ],
            "exact_size_alpha_postprocess": {
                "prompt_ids": [
                    "a56696d2-74b2-4f5d-bea9-021e53977c58",
                    "1a13b123-68ff-467e-882b-0534dab07d59",
                ],
                "outputs": [
                    {
                        "artifact": _artifact(exact_1, "Qwen candidate 1 fitted and masked"),
                        "alpha_comparison": compare_to_authoritative_2x(source, exact_1),
                    },
                    {
                        "artifact": _artifact(exact_2, "Qwen candidate 2 fitted and masked"),
                        "alpha_comparison": compare_to_authoritative_2x(source, exact_2),
                    },
                ],
            },
            "visible_review": {
                "preserved": [
                    "recognizable overall window and palette",
                    "BGM, Effect, Skin, on, opaque, attack, skill, and item labels",
                    "checked and unchecked checkbox pattern",
                    "BGM slider handle is approximately retained",
                    "Japanese title and bottom label remain recognizable but were not asserted character-exact by automated OCR",
                ],
                "drift": [
                    "Effect slider handle moved left in both candidates",
                    "outer border and crop geometry changed",
                    "raw outputs are opaque RGB at 2048 x 1024, not the 3144 x 1436 RGBA target",
                    "exact-size alpha postprocessing cannot repair interior geometry drift",
                ],
                "finding": (
                    "Qwen did not improve this pure enlargement over the native "
                    "nearest-exact result. No additional paid outputs are justified."
                ),
            },
        },
        "contact_sheet": _artifact(contact_sheet, "human comparison evidence"),
        "human_visual_approval": "pending",
    }
    (root / "run.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (root / "report.md").write_text(
        "# Issue #34 result\n\n"
        "The native nearest-exact graph is the strongest enlargement in this test. "
        "It keeps every RGB pixel and control position exact at 2x. ComfyUI changes "
        "some very faint alpha-fringe pixels because of its intermediate mask precision.\n\n"
        "The first proposed graph was wrong for an uploaded PNG: `LoadImage` had already "
        "separated RGB from alpha, so splitting RGB again returned no useful mask. The "
        "correct graph uses `LoadImage` output 1 as the mask.\n\n"
        "Two paid source-only Qwen outputs cost $0.083. Both are recognizable, but both "
        "move the Effect slider handle and change the outer geometry. Reapplying the "
        "source mask fixes size and transparency only; it does not fix those interior "
        "changes. The initial pair answered the question, so no more paid outputs were run.\n\n"
        "Human visual approval is still pending.\n",
        encoding="utf-8",
    )


def write_experiment_inputs(root: Path) -> None:
    """Persist auditable workflows and the pre-submission paid-run plan."""

    deterministic = root / "deterministic"
    qwen = root / "qwen"
    deterministic.mkdir(parents=True, exist_ok=True)
    qwen.mkdir(parents=True, exist_ok=True)
    for method in ("nearest-exact", "lanczos"):
        workflow = build_alpha_resize_workflow(
            reference_filename="issue-34-options-window-source.png",
            filename_prefix=f"issue-34/{method}-alpha-2x",
            image_method=method,
        )
        (deterministic / f"{method}-alpha-2x.api.json").write_text(
            json.dumps(workflow, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        failed_workflow = build_failed_split_after_load_workflow(
            reference_filename="issue-34-options-window-source.png",
            filename_prefix=f"issue-34/{method}-2x",
            image_method=method,
        )
        (deterministic / f"failed-split-{method}-2x.api.json").write_text(
            json.dumps(failed_workflow, indent=2, ensure_ascii=False, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )

    brief = build_qwen_brief()
    workflow = build_qwen_workflow(
        brief,
        reference_filename="issue-34-options-window-source.png",
    )
    plan = {
        "schema_version": 1,
        "issue": 34,
        "classification": "comparison evidence plan",
        "experimental_question": (
            "Can a source-only Qwen Image 3 Pro Render Pass produce a more useful "
            "enlarged reconstruction than native interpolation while preserving the "
            "window's text, controls, geometry, and visual character?"
        ),
        "stopping_condition": (
            "Inspect the initial pair before requesting more output. Continue only "
            "for a named question left unanswered by both candidates."
        ),
        "provider": "openrouter",
        "model": "qwen/qwen-image-3-pro",
        "requested_outputs": 2,
        "cost": {
            "basis": "Issue #2's latest four-output run cost $0.169 total",
            "estimated_cost_per_output_usd": 0.04225,
            "pre_submission_estimate_usd": 0.0845,
        },
        "source": {
            "path": "artifacts/issue-34/alpha-window-2x/source/options-window-source.png",
            "sha256": SOURCE_SHA256,
            "size": list(SOURCE_SIZE),
            "role": "only Qwen image input and immutable Reference Screen",
        },
        "target_size": list(TARGET_SIZE),
        "settings": brief["output"],
        "selection_guide_used": False,
    }
    files = {
        qwen / "brief.json": brief,
        qwen / "plan.json": plan,
        qwen / "source-only-v001.api.json": workflow,
    }
    for candidate_number in (1, 2):
        exact_workflow = build_qwen_exact_alpha_workflow(
            candidate_filename=f"issue-34-qwen-raw-{candidate_number:02d}.png",
            reference_filename="issue-34-options-window-source.png",
            candidate_number=candidate_number,
        )
        files[qwen / f"exact-alpha-v001-candidate-{candidate_number:02d}.api.json"] = (
            exact_workflow
        )
    for path, value in files.items():
        path.write_text(
            json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    (qwen / "prompt.txt").write_text(
        compile_edit_brief(brief).prompt + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--finalize", action="store_true")
    args = parser.parse_args()
    write_experiment_inputs(args.root)
    if args.finalize:
        finalize_experiment(args.root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
