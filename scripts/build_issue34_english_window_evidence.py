"""Build the revised Issue #34 English structural-edit experiment."""

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
SEED = 2026082602
BASELINE_COMMIT = "27bee23bf6089f5587ec8994eab7a87621b2dd94"
EVIDENCE_COMMIT = "0f466d23bfed38836758413ae2cb6fa08880b58f"
REVIEW_EVIDENCE_COMMIT = "6b1688a1d07142d3b1128f5ae4791fb421288fc1"


def build_english_edit_brief() -> dict[str, Any]:
    """Describe the English, one-slider, uniformly reflowed target window."""

    return {
        "provider": "openrouter",
        "model": "qwen/qwen-image-3-pro",
        "objective": (
            "Regenerate the complete Reference Screen as an English options window "
            "at exactly twice the source width and height. Remove one complete "
            "control row and reflow the remaining controls uniformly. This is a "
            "structural interface edit, not a simple upscale or redesign."
        ),
        "reference_role": (
            "Reference 1 is the only image input and the authority for the window "
            "theme, pixel-era raster style, palette, borders, controls, and states."
        ),
        "preservation_invariants": [
            "Keep the entire transparent window visible with no surrounding scene or crop.",
            "Keep the magenta outer frame, blue-grey title bar, white panel, checker-shadow edge, left tabs, dropdown, bevels, and limited palette.",
            "Keep authentic enlarged aliased raster lettering and controls; do not modernize, vectorize, anti-alias into a contemporary UI, or invent decoration.",
            "Keep the BGM slider handle and retained checkbox states in the same relative state as the Reference Screen.",
        ],
        "regions": [
            {
                "name": "title",
                "change": "Replace the Japanese title with the English word Options.",
            },
            {
                "name": "second slider row",
                "change": (
                    "Remove the complete Effect row: its label, left and right arrows, "
                    "slider track, handle, checkbox, and adjacent on label."
                ),
            },
            {
                "name": "remaining body",
                "change": (
                    "Reflow the BGM, Skin, and bottom-option rows with intentional, "
                    "even vertical spacing; leave no Effect-shaped blank gap."
                ),
            },
            {
                "name": "bottom Japanese label",
                "change": "Replace the Japanese label with the English word Snap.",
            },
        ],
        "exact_copy": [
            {"region": "title bar", "text": "Options"},
            {"region": "left tab", "text": "option"},
            {"region": "left tab", "text": "info"},
            {"region": "remaining slider", "text": "BGM"},
            {"region": "dropdown", "text": "Skin"},
            {"region": "BGM checkbox", "text": "on"},
            {"region": "bottom option", "text": "opaque"},
            {"region": "bottom option", "text": "Snap"},
            {"region": "bottom option", "text": "attack"},
            {"region": "bottom option", "text": "skill"},
            {"region": "bottom option", "text": "item"},
        ],
        "style": [
            "Faithful late-1990s or early-2000s Japanese PC game options dialog translated into English.",
            "Crisp 2x raster pixels, restrained bevels, original geometry language, and original colors.",
        ],
        "asset_rules": [
            "Return exactly one complete window per output.",
            "Use no image other than Reference 1 and add no mask, guide, annotation, or highlighted region.",
            "The review canvas is exactly 3144 by 1436 with the source composition enlarged to fill it.",
        ],
        "negative_constraints": [
            "No Effect word, Effect slider, second slider track, second slider arrows, second handle, second checkbox, or second on label.",
            "No Japanese text remains anywhere in the edited interface.",
            "No green guide, mask color, selection outline, annotation, glow, or donor image.",
            "No empty horizontal band where the Effect row was removed.",
            "No new words, icons, controls, decoration, background, or content.",
        ],
        "quality_checks": [
            "Every Exact Copy string is legible and character-for-character correct.",
            "There is exactly one slider, labeled BGM, and no Effect row remains.",
            "BGM, Skin, and bottom options use even, intentional vertical spacing.",
            "The complete window silhouette, title bar, tabs, dropdown, and bottom controls remain recognizable as the same interface.",
        ],
        "output": {
            "resolution": "2K",
            "aspect_ratio": "2:1",
            "count": 2,
            "seed": SEED,
        },
    }


def build_direct_baseline_workflow(
    brief: dict[str, Any],
    *,
    reference_filename: str,
) -> dict[str, Any]:
    """Build the source-only baseline with no visual preprocessing nodes."""

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
                "filename_prefix": "issue-34/english-v002/direct-baseline",
                "images": ["2", 0],
            },
        },
        "4": {
            "class_type": "SaveText",
            "inputs": {
                "filename_prefix": "issue-34/english-v002/direct-baseline-metadata",
                "format": "json",
                "text": ["2", 1],
            },
        },
    }


def build_node_assisted_workflow(
    *,
    candidate_filename: str,
    source_filename: str,
    candidate_number: int,
) -> dict[str, Any]:
    """Fit one raw candidate and apply the source-derived exterior alpha."""

    dimensions = {
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
                **dimensions,
                "scale_method": "lanczos",
            },
        },
        "3": {
            "class_type": "LoadImage",
            "inputs": {"image": source_filename},
        },
        "4": {
            "class_type": "ResizeImageMaskNode",
            "inputs": {
                "input": ["3", 1],
                **dimensions,
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
                    "issue-34/english-v002/node-assisted-"
                    f"candidate-{candidate_number:02d}"
                ),
                "images": ["5", 0],
            },
        },
    }


def analyze_image(path: Path) -> dict[str, Any]:
    """Record image identity, dimensions, mode, and alpha statistics."""

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


def compare_alpha_to_source(
    source_path: Path,
    candidate_path: Path,
) -> dict[str, int]:
    """Compare candidate alpha to the exact nearest-neighbor 2x source alpha."""

    with Image.open(source_path) as opened:
        source_alpha = (
            opened.convert("RGBA")
            .resize(TARGET_SIZE, Image.Resampling.NEAREST)
            .getchannel("A")
        )
    with Image.open(candidate_path) as opened:
        candidate = opened.convert("RGBA")
        candidate_alpha = candidate.getchannel("A")
    if candidate.size != TARGET_SIZE:
        raise ValueError(f"candidate size must be {TARGET_SIZE}, got {candidate.size}")
    pairs = zip(source_alpha.getdata(), candidate_alpha.getdata(), strict=True)
    values = list(pairs)
    return {
        "alpha_value_errors": sum(source != output for source, output in values),
        "transparent_membership_errors": sum(
            (source == 0) != (output == 0) for source, output in values
        ),
        "opaque_membership_errors": sum(
            (source == 255) != (output == 255) for source, output in values
        ),
    }


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    font_path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
    if font_path.exists():
        return ImageFont.truetype(font_path.as_posix(), size)
    return ImageFont.load_default()


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
    """Build a labeled checker-backed comparison for human review."""

    tile_width, image_height, label_height, header_height = 1200, 600, 76, 154
    rows = (len(items) + 1) // 2
    sheet = Image.new(
        "RGB",
        (tile_width * 2, header_height + rows * (image_height + label_height)),
        (35, 38, 44),
    )
    draw = ImageDraw.Draw(sheet)
    draw.text(
        (22, 16),
        "Issue #34 v002 — real English structural-edit test",
        font=_font(34),
        fill="white",
    )
    draw.text(
        (22, 66),
        "Baseline: direct Qwen | Assisted: exact size + source alpha only",
        font=_font(23),
        fill=(220, 224, 232),
    )
    draw.text(
        (22, 106),
        f"Source SHA-256: {SOURCE_SHA256}",
        font=_font(18),
        fill=(190, 198, 212),
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
        draw.text(
            (x + 18, y + image_height + 14),
            label,
            font=_font(24),
            fill="white",
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path)


def _file_artifact(path: Path, role: str) -> dict[str, Any]:
    return {
        "path": path.as_posix(),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "role": role,
    }


def finalize_experiment(root: Path) -> None:
    """Write the comparison sheet, run manifest, and plain-language result."""

    source = Path(
        "artifacts/issue-34/alpha-window-2x/source/options-window-source.png"
    )
    raw = [root / f"raw/candidate-{number:02d}.png" for number in (1, 2)]
    assisted = [
        root / f"node-assisted/candidate-{number:02d}.png" for number in (1, 2)
    ]
    required = [source, *raw, *assisted, root / "provider-metadata.json"]
    missing = [path.as_posix() for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"missing revised experiment artifact(s): {missing}")

    contact_sheet = root / "comparison-v002.png"
    build_contact_sheet(
        [
            ("Reference Screen — failed v001 asked only for upscale", source),
            ("Direct baseline 1 — model changed structure", raw[0]),
            ("Direct baseline 2 — cleaner structural edit", raw[1]),
            ("Node-assisted 1 — exact size + source alpha", assisted[0]),
            ("Node-assisted 2 — exact size + source alpha", assisted[1]),
        ],
        contact_sheet,
    )
    provider_metadata = json.loads((root / "provider-metadata.json").read_text())
    manifest = {
        "schema_version": 1,
        "issue": 34,
        "experiment": "english-structural-edit-v002",
        "classification": "comparison evidence and reproducibility metadata",
        "git": {
            "baseline_commit": BASELINE_COMMIT,
            "candidate_evidence_commit": EVIDENCE_COMMIT,
            "review_evidence_commit": REVIEW_EVIDENCE_COMMIT,
            "note": (
                "The candidate commit contains the exact workflows, provider record, "
                "and outputs. The review commit adds the corrected per-candidate rubric, "
                "live validation, report, and tests. This later metadata commit records "
                "both exact SHAs."
            ),
        },
        "prior_experiment": {
            "path": "artifacts/issue-34/alpha-window-2x",
            "classification": "failed test design",
            "reason": (
                "It asked only for enlargement, so it did not test a meaningful "
                "generative or node-assisted edit."
            ),
        },
        "source": {**analyze_image(source), "role": "immutable Reference Screen"},
        "target_size": list(TARGET_SIZE),
        "direct_baseline": {
            "provider": "openrouter",
            "model": "qwen/qwen-image-3-pro",
            "prompt_id": "179dd12b-bd20-430b-a5f3-3f072823c196",
            "seed": SEED,
            "requested_outputs": 2,
            "completed_outputs": 2,
            "pre_submission_estimate_usd": 0.083,
            "actual_cost_usd": 0.083,
            "duration_seconds": 92.24,
            "usage": provider_metadata.get("usage", {}),
            "reference_count": 1,
            "visual_preprocessing_or_guide": False,
            "workflow": _file_artifact(
                root / "direct-baseline.api.json",
                "direct source-only baseline workflow",
            ),
            "outputs": [
                {**analyze_image(path), "role": f"raw baseline candidate {index}"}
                for index, path in enumerate(raw, start=1)
            ],
        },
        "node_assisted_review": {
            "model_calls": 0,
            "nodes": ["ResizeImageMaskNode", "JoinImageWithAlpha"],
            "scope": "exact target size and source-derived exterior alpha only",
            "prompt_ids": [
                "ccd19935-f1d5-422a-bd3f-5109993bcec5",
                "f9ad2767-25bb-48a3-9cfd-3ad185878e30",
            ],
            "workflows": [
                _file_artifact(
                    root / f"node-assisted-candidate-{number:02d}.api.json",
                    f"candidate {number} exact-size and source-alpha workflow",
                )
                for number in (1, 2)
            ],
            "outputs": [
                {
                    **analyze_image(path),
                    "role": f"node-assisted review candidate {index}",
                    "alpha_comparison": compare_alpha_to_source(source, path),
                }
                for index, path in enumerate(assisted, start=1)
            ],
            "finding": (
                "The nodes provide exact dimensions and a transparent exterior. "
                "They do not alter or improve the generated English text, removed "
                "row, or internal reflow."
            ),
        },
        "visible_review": {
            "live_validation": _file_artifact(
                root / "live-validation.json",
                "live ComfyUI health, schema, validation, and execution evidence",
            ),
            "ocr": _file_artifact(
                root / "ocr.txt",
                "inconclusive Tesseract readback for human context only",
            ),
            "shared_successes": [
                "Options and Snap replace the two Japanese labels",
                "the complete Effect row is absent",
                "one BGM slider remains with an approximately preserved handle position",
                "BGM, Skin, and bottom controls are redistributed without an Effect-shaped gap",
                "the magenta frame, title bar, left tabs, dropdown, checkbox pattern, and pixel-era theme remain recognizable",
            ],
            "candidate_1": {
                "classification": "partial evidence; not a passing candidate",
                "criteria": {
                    "exact_english_copy": "pending human review; OCR inconclusive",
                    "complete_effect_row_removal": "pass",
                    "preserved_bgm_state": "fail; slider handle moved left",
                    "uniform_reflow": "partial; no empty Effect gap, but spacing is less even",
                    "source_theme": "pass by visual inspection",
                    "crop_and_geometry": "partial; raw provider aspect differs and outer geometry changed",
                },
            },
            "candidate_2": {
                "classification": "stronger review candidate; human approval pending",
                "criteria": {
                    "exact_english_copy": "pending human review; OCR inconclusive",
                    "complete_effect_row_removal": "pass",
                    "preserved_bgm_state": "pass by visual inspection",
                    "uniform_reflow": "pass by visual inspection",
                    "source_theme": "pass by visual inspection",
                    "crop_and_geometry": "partial; node arm restores exact canvas and exterior alpha but not interior pixel identity",
                },
            },
            "limitations": [
                "Tesseract OCR is inconclusive on the aliased pixel font; Exact Copy still requires human visual review",
                "the raw 2:1 provider canvas is horizontally fitted to the 2.19:1 target",
                "source-alpha postprocessing retains the known low-alpha precision limitation",
            ],
            "stronger_review_candidate": 2,
        },
        "stopping_reason": (
            "The initial pair answers the revised question: Qwen performs the real "
            "structural edit, while the nodes help only with canvas and alpha."
        ),
        "contact_sheet": {
            **analyze_image(contact_sheet),
            "role": "human comparison evidence",
        },
        "human_visual_approval": "pending",
    }
    _write_json(root / "run.json", manifest)
    (root / "report.md").write_text(
        "# Issue #34 revised result\n\n"
        "The first experiment was a failed test design because it asked only for an "
        "upscale. This v002 experiment requires real changes: English copy, complete "
        "Effect-row removal, and uniform reflow.\n\n"
        "Candidate 1 is partial evidence: it removes the Effect row, but moves the BGM "
        "handle left and has weaker spacing. Candidate 2 is the cleaner result because "
        "its remaining controls are more evenly aligned and its BGM state is closer to "
        "the source. It is the stronger review candidate, not an approved output.\n\n"
        "The ComfyUI nodes help with delivery rather than design. They convert each "
        "2048 x 1024 opaque raw output to the exact 3144 x 1436 review size and apply "
        "the source-derived exterior alpha. They do not improve the English text, "
        "slider removal, or internal spacing.\n\n"
        "The two-output OpenRouter run cost $0.083. No second paid pair was run because "
        "the initial pair answered the question. Tesseract OCR was inconclusive on "
        "the pixel font, so exact-copy and visual approval remain human decisions.\n",
        encoding="utf-8",
    )
def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_experiment_inputs(root: Path) -> None:
    """Persist the approved brief, plan, and exact workflows before submission."""

    brief = build_english_edit_brief()
    baseline = build_direct_baseline_workflow(
        brief,
        reference_filename="issue-34-options-window-source.png",
    )
    plan = {
        "schema_version": 1,
        "issue": 34,
        "classification": "pre-submission comparison evidence plan",
        "experimental_question": (
            "Can source-only Qwen Image 3 Pro perform the English translation, "
            "complete Effect-row removal, and uniform reflow while preserving the "
            "Reference Screen theme; and do exact-size/alpha nodes add review value?"
        ),
        "provider": "openrouter",
        "model": "qwen/qwen-image-3-pro",
        "requested_outputs": 2,
        "seed": SEED,
        "cost": {
            "basis": "Issue #34 v001 two-output run cost $0.083",
            "pre_submission_estimate_usd": 0.083,
        },
        "source": {
            "path": "artifacts/issue-34/alpha-window-2x/source/options-window-source.png",
            "sha256": SOURCE_SHA256,
            "size": list(SOURCE_SIZE),
            "role": "only baseline image input and immutable Reference Screen",
        },
        "target_size": list(TARGET_SIZE),
        "stopping_condition": (
            "Inspect both baseline candidates and their node-assisted review outputs. "
            "Stop if they answer whether the edit and nodes work. Record a diagnosed "
            "brief weakness before using the separately authorized revised pair."
        ),
        "node_hypothesis": (
            "ResizeImageMaskNode and JoinImageWithAlpha may fix canvas dimensions and "
            "exterior transparency only; they cannot fix text or internal layout."
        ),
    }
    _write_json(root / "brief.json", brief)
    _write_json(root / "plan.json", plan)
    _write_json(root / "direct-baseline.api.json", baseline)
    for candidate_number in (1, 2):
        _write_json(
            root / f"node-assisted-candidate-{candidate_number:02d}.api.json",
            build_node_assisted_workflow(
                candidate_filename=(
                    f"issue-34-english-v002-raw-{candidate_number:02d}.png"
                ),
                source_filename="issue-34-options-window-source.png",
                candidate_number=candidate_number,
            ),
        )
    (root / "prompt.txt").write_text(
        compile_edit_brief(brief).prompt + "\n",
        encoding="utf-8",
    )
    source_path = (
        Path("artifacts/issue-34/alpha-window-2x/source/options-window-source.png")
    )
    if source_path.exists():
        actual = hashlib.sha256(source_path.read_bytes()).hexdigest()
        if actual != SOURCE_SHA256:
            raise ValueError(f"Reference Screen hash mismatch: {actual}")


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
